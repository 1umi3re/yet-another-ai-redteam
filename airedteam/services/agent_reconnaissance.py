from __future__ import annotations

import json
import re
from typing import Any

from sqlalchemy import func, select

from airedteam.core.types import Message, Prompt, Response
from airedteam.engine.factory import build_target
from airedteam.engine.input_limits import apply_target_input_limit
from airedteam.storage.models import TargetReconReport

DEFAULT_MAX_ROUNDS = 10
ALLOWED_PROBE_TYPES = {
    "capability_question",
    "public_read_only",
    "synthetic_task",
    "boundary_question",
    "session_memory",
}
CAPABILITY_KINDS = {"skill", "tool", "mcp_server", "mcp_resource", "integration", "unknown"}
CAPABILITY_STATUSES = {"claimed", "verified", "refuted", "inconclusive", "claimed_unverified"}
CLASSIFICATIONS = {"chat_app", "service_agent", "tool_agent", "unknown"}
_UNSAFE_ENGLISH = re.compile(
    r"\b(send|email|message|post|publish|delete|remove|write|upload|book|reserve|purchase|buy|pay|transfer|"
    r"create|update|edit|submit|execute|run command|shell|credential|password|secret|private file|private email|"
    r"calendar event|crm record)\b",
    re.IGNORECASE,
)
_UNSAFE_CJK = (
    "发送", "删除", "上传", "预订", "购买", "支付", "转账", "创建", "修改", "密码", "密钥", "私人文件", "邮件内容"
)


def _extract_json(text: str) -> dict[str, Any]:
    match = re.search(r"\{.*\}", text or "", re.DOTALL)
    if not match:
        raise ValueError("model response did not contain a JSON object")
    try:
        value = json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        raise ValueError(f"model returned invalid JSON: {exc.msg}") from exc
    if not isinstance(value, dict):
        raise ValueError("model JSON response must be an object")
    return value


def _model_name(runtime_cfg: dict) -> str:
    model = str((runtime_cfg.get("params") or {}).get("model") or "").strip()
    if not model:
        raise ValueError("target config requires params.model for reconnaissance")
    return model


def _public(row: TargetReconReport) -> dict[str, Any]:
    return {
        "id": row.id,
        "target_config_id": row.target_config_id,
        "target_model": row.target_model,
        "generator_config_id": row.generator_config_id,
        "generator_model": row.generator_model,
        "version": row.version,
        "status": row.status,
        "report": row.report_json,
        "error": row.error,
        "has_trace": bool(row.trace_blob_path),
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


def _raw_metadata(response: Response) -> dict[str, Any]:
    raw = response.raw if isinstance(response.raw, dict) else {}
    summary: dict[str, Any] = {"keys": sorted(str(key) for key in raw.keys())[:30]}
    choices = raw.get("choices")
    if isinstance(choices, list) and choices and isinstance(choices[0], dict):
        first = choices[0]
        summary["finish_reason"] = first.get("finish_reason")
        message = first.get("message") if isinstance(first.get("message"), dict) else {}
        summary["message_keys"] = sorted(str(key) for key in message.keys())[:20]
        calls = message.get("tool_calls")
        if isinstance(calls, list):
            summary["tool_call_names"] = [
                str((call.get("function") or {}).get("name") or call.get("name") or "unknown")
                for call in calls
                if isinstance(call, dict)
            ][:20]
    content = raw.get("content")
    if isinstance(content, list):
        summary["content_types"] = [
            str(item.get("type") or "unknown") for item in content if isinstance(item, dict)
        ][:20]
        summary["tool_names"] = [
            str(item.get("name"))
            for item in content
            if isinstance(item, dict) and item.get("type") in {"tool_use", "tool_result"} and item.get("name")
        ][:20]
    return summary


def _bounded_confidence(value: Any) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return 0.0


def _normalise_report(value: dict[str, Any]) -> dict[str, Any]:
    language = value.get("primary_language") if isinstance(value.get("primary_language"), dict) else {}
    interaction = value.get("interaction") if isinstance(value.get("interaction"), dict) else {}
    capabilities = []
    seen_ids: set[str] = set()
    for index, raw in enumerate(value.get("capabilities") or []):
        if not isinstance(raw, dict):
            continue
        capability_id = re.sub(r"[^A-Za-z0-9_.:-]+", "-", str(raw.get("id") or f"capability-{index + 1}"))[:100]
        if not capability_id or capability_id in seen_ids:
            continue
        seen_ids.add(capability_id)
        kind = str(raw.get("kind") or "unknown")
        status = str(raw.get("status") or "claimed")
        capabilities.append(
            {
                "id": capability_id,
                "name": str(raw.get("name") or capability_id)[:200],
                "kind": kind if kind in CAPABILITY_KINDS else "unknown",
                "description": str(raw.get("description") or "")[:2000],
                "status": status if status in CAPABILITY_STATUSES else "claimed",
                "confidence": _bounded_confidence(raw.get("confidence")),
                "evidence": [str(item)[:1000] for item in (raw.get("evidence") or []) if str(item).strip()][:20],
                "safety_boundary": str(raw.get("safety_boundary") or "unknown")[:2000],
            }
        )
    classification = str(value.get("classification") or "unknown")
    return {
        "classification": classification if classification in CLASSIFICATIONS else "unknown",
        "primary_language": {
            "code": str(language.get("code") or "und")[:40],
            "name": str(language.get("name") or "Unknown")[:100],
        },
        "service_topics": [str(item)[:500] for item in (value.get("service_topics") or []) if str(item).strip()][:50],
        "capabilities": capabilities,
        "interaction": {
            "multi_turn": str(interaction.get("multi_turn") or "unknown")[:40],
            "memory": str(interaction.get("memory") or "unknown")[:40],
            "authentication": str(interaction.get("authentication") or "unknown")[:1000],
            "confirmation": str(interaction.get("confirmation") or "unknown")[:1000],
            "limitations": [str(item)[:1000] for item in (interaction.get("limitations") or []) if str(item).strip()][
                :30
            ],
        },
        "boundary_findings": [
            str(item)[:1000] for item in (value.get("boundary_findings") or []) if str(item).strip()
        ][:50],
        "summary": str(value.get("summary") or "")[:5000],
        "confidence": _bounded_confidence(value.get("confidence")),
    }


def _server_probe_safe(probe_type: str, probe: str) -> tuple[bool, str | None]:
    if probe_type not in ALLOWED_PROBE_TYPES:
        return False, "probe type is not allowed"
    text = str(probe or "").strip()
    if not text or len(text) > 2000:
        return False, "probe must contain 1 to 2000 characters"
    if _UNSAFE_ENGLISH.search(text) or any(term in text for term in _UNSAFE_CJK):
        return False, "server denylist detected a potentially private or state-changing request"
    return True, None


def _safety_passed(value: dict[str, Any]) -> bool:
    return (
        value.get("safe") is True
        and value.get("read_only") is True
        and value.get("public_or_synthetic") is True
        and value.get("state_change") is False
        and value.get("sensitive_data") is False
    )


def _merge_judgement(report: dict[str, Any], judgement: dict[str, Any]) -> None:
    capability_by_id = {item["id"]: item for item in report["capabilities"]}
    for update in judgement.get("capability_updates") or []:
        if not isinstance(update, dict) or str(update.get("id")) not in capability_by_id:
            continue
        capability = capability_by_id[str(update["id"])]
        status = str(update.get("status") or capability["status"])
        if status in CAPABILITY_STATUSES:
            capability["status"] = status
        capability["confidence"] = _bounded_confidence(update.get("confidence"))
        evidence = str(update.get("evidence") or "").strip()
        if evidence and evidence not in capability["evidence"]:
            capability["evidence"].append(evidence[:1000])
        boundary = str(update.get("safety_boundary") or "").strip()
        if boundary:
            capability["safety_boundary"] = boundary[:2000]
    for finding in judgement.get("boundary_findings") or []:
        finding = str(finding).strip()[:1000]
        if finding and finding not in report["boundary_findings"]:
            report["boundary_findings"].append(finding)
    interaction = judgement.get("interaction_updates")
    if isinstance(interaction, dict):
        for key in ("multi_turn", "memory", "authentication", "confirmation"):
            if interaction.get(key) not in (None, ""):
                report["interaction"][key] = str(interaction[key])[:1000]
        limitations = interaction.get("limitations")
        if isinstance(limitations, list):
            report["interaction"]["limitations"] = list(
                dict.fromkeys(report["interaction"]["limitations"] + [str(item)[:1000] for item in limitations])
            )[:30]


def _preserve_judged_evidence(draft: dict[str, Any], final: dict[str, Any]) -> dict[str, Any]:
    final_by_id = {item["id"]: item for item in final["capabilities"]}
    for source in draft["capabilities"]:
        destination = final_by_id.get(source["id"])
        if destination is None:
            copied = dict(source)
            copied["evidence"] = list(source["evidence"])
            final["capabilities"].append(copied)
            continue
        if source["status"] != "claimed":
            destination["status"] = source["status"]
            destination["confidence"] = source["confidence"]
        destination["evidence"] = list(dict.fromkeys(source["evidence"] + destination["evidence"]))[:20]
        if source["safety_boundary"] != "unknown":
            destination["safety_boundary"] = source["safety_boundary"]
    final["boundary_findings"] = list(
        dict.fromkeys(draft["boundary_findings"] + final["boundary_findings"])
    )[:50]
    return final


class AgentReconnaissanceService:
    def __init__(self, session_factory, blob_store, target_configs, prompt_assets) -> None:
        self._sf = session_factory
        self._blob = blob_store
        self._targets = target_configs
        self._prompt_assets = prompt_assets

    def _build_target(self, runtime_cfg: dict):
        target = build_target(runtime_cfg)
        apply_target_input_limit(target, runtime_cfg)
        return target

    async def list_for_target(self, target_config_id: str) -> list[dict[str, Any]]:
        if await self._targets.get(target_config_id) is None:
            raise KeyError(target_config_id)
        async with self._sf() as session:
            rows = (
                (
                    await session.execute(
                        select(TargetReconReport)
                        .where(TargetReconReport.target_config_id == target_config_id)
                        .order_by(TargetReconReport.version.desc())
                    )
                )
                .scalars()
                .all()
            )
            return [_public(row) for row in rows]

    async def get(self, report_id: str) -> TargetReconReport | None:
        async with self._sf() as session:
            return await session.get(TargetReconReport, report_id)

    async def get_trace(self, report_id: str) -> dict[str, Any]:
        row = await self.get(report_id)
        if row is None:
            raise KeyError(report_id)
        if not row.trace_blob_path:
            return {}
        return json.loads((await self._blob.get(row.trace_blob_path)).decode("utf-8"))

    async def run(
        self,
        target_config_id: str,
        generator_config_id: str,
        *,
        max_rounds: int = DEFAULT_MAX_ROUNDS,
    ) -> dict[str, Any]:
        try:
            max_rounds = int(max_rounds)
        except (TypeError, ValueError):
            raise ValueError("max_rounds must be an integer from 1 to 10") from None
        if not 1 <= max_rounds <= DEFAULT_MAX_ROUNDS:
            raise ValueError("max_rounds must be an integer from 1 to 10")
        if target_config_id == generator_config_id:
            raise ValueError("generator target must be different from the tested target")
        target_cfg = await self._targets.resolve_for_runtime(target_config_id)
        generator_cfg = await self._targets.resolve_for_runtime(generator_config_id)
        target_model = _model_name(target_cfg)
        generator_model = _model_name(generator_cfg)
        target_row = await self._targets.get(target_config_id)

        async with self._sf() as session:
            current = await session.scalar(
                select(func.max(TargetReconReport.version)).where(
                    TargetReconReport.target_config_id == target_config_id,
                    TargetReconReport.target_model == target_model,
                )
            )
            row = TargetReconReport(
                target_config_id=target_config_id,
                target_model=target_model,
                generator_config_id=generator_config_id,
                generator_model=generator_model,
                version=int(current or 0) + 1,
                status="running",
            )
            session.add(row)
            await session.commit()
            await session.refresh(row)

        target = generator = None
        trace: dict[str, Any] = {
            "target_config_id": target_config_id,
            "target_model": target_model,
            "generator_config_id": generator_config_id,
            "generator_model": generator_model,
            "max_rounds": max_rounds,
            "initial": {},
            "rounds": [],
        }
        try:
            target = self._build_target(target_cfg)
            generator = self._build_target(generator_cfg)
            target_name = target_row.name if target_row is not None else getattr(target, "name", target_model)
            initial_snapshot = await self._prompt_assets.render("agent_recon.initial.v1", {"target_name": target_name})
            messages = [Message(role="user", text=initial_snapshot["rendered_text"])]
            initial_response = await target.chat(messages)
            messages.append(Message(role="assistant", text=initial_response.text))
            initial_metadata = _raw_metadata(initial_response)
            trace["initial"] = {
                "prompt": initial_snapshot,
                "response": initial_response.text,
                "raw_metadata": initial_metadata,
            }
            analysis_snapshot = await self._prompt_assets.render(
                "agent_recon.analyze.v1",
                {
                    "target_name": target_name,
                    "target_response": initial_response.text,
                    "raw_metadata": json.dumps(initial_metadata, ensure_ascii=False),
                },
            )
            analysis_response = await generator.generate(Prompt(text=analysis_snapshot["rendered_text"]))
            report = _normalise_report(_extract_json(analysis_response.text))
            trace["initial"].update(
                {
                    "analysis_prompt": analysis_snapshot,
                    "analysis_response": analysis_response.text,
                    "parsed_report": report,
                }
            )
            evidence: list[dict[str, Any]] = []
            completed_probe_types: set[str] = set()
            target_language = report["primary_language"]["name"] + " (" + report["primary_language"]["code"] + ")"

            for round_number in range(1, max_rounds + 1):
                round_trace: dict[str, Any] = {"number": round_number}
                planning_snapshot = await self._prompt_assets.render(
                    "agent_recon.plan_probe.v1",
                    {
                        "target_language": target_language,
                        "round_number": round_number,
                        "max_rounds": max_rounds,
                        "report": json.dumps(report, ensure_ascii=False),
                        "evidence": json.dumps(evidence, ensure_ascii=False),
                    },
                )
                planning_response = await generator.generate(Prompt(text=planning_snapshot["rendered_text"]))
                plan = _extract_json(planning_response.text)
                round_trace.update(
                    {"planning_prompt": planning_snapshot, "planning_response": planning_response.text, "plan": plan}
                )
                coverage_complete = bool(completed_probe_types & {"boundary_question"}) and all(
                    item["status"] != "claimed" for item in report["capabilities"]
                )
                if plan.get("done") is True and coverage_complete:
                    round_trace["stopped_early"] = True
                    trace["rounds"].append(round_trace)
                    break
                if plan.get("done") is True:
                    round_trace["skipped"] = "planner requested completion before minimum coverage"
                    trace["rounds"].append(round_trace)
                    continue

                probe_type = str(plan.get("probe_type") or "")
                probe = str(plan.get("probe") or "").strip()
                capability_id = str(plan.get("capability_id") or "")
                server_safe, server_reason = _server_probe_safe(probe_type, probe)
                round_trace["server_safety"] = {"safe": server_safe, "reason": server_reason}
                if not server_safe:
                    round_trace["skipped"] = server_reason
                    trace["rounds"].append(round_trace)
                    continue

                safety_snapshot = await self._prompt_assets.render(
                    "agent_recon.safety_check.v1", {"probe_type": probe_type, "probe": probe}
                )
                safety_response = await generator.generate(Prompt(text=safety_snapshot["rendered_text"]))
                safety = _extract_json(safety_response.text)
                round_trace["generator_safety"] = {
                    "prompt": safety_snapshot,
                    "response": safety_response.text,
                    "parsed": safety,
                }
                if not _safety_passed(safety):
                    round_trace["skipped"] = "generator safety gate rejected the probe"
                    trace["rounds"].append(round_trace)
                    continue

                messages.append(Message(role="user", text=probe))
                target_response = await target.chat(list(messages))
                messages.append(Message(role="assistant", text=target_response.text))
                raw_metadata = _raw_metadata(target_response)
                judgement_snapshot = await self._prompt_assets.render(
                    "agent_recon.judge_probe.v1",
                    {
                        "report": json.dumps(report, ensure_ascii=False),
                        "probe_type": probe_type,
                        "capability_id": capability_id,
                        "probe": probe,
                        "target_response": target_response.text,
                        "raw_metadata": json.dumps(raw_metadata, ensure_ascii=False),
                    },
                )
                judgement_response = await generator.generate(Prompt(text=judgement_snapshot["rendered_text"]))
                judgement = _extract_json(judgement_response.text)
                _merge_judgement(report, judgement)
                completed_probe_types.add(probe_type)
                evidence.append(
                    {
                        "round": round_number,
                        "probe_type": probe_type,
                        "capability_id": capability_id,
                        "probe": probe,
                        "response": target_response.text,
                        "raw_metadata": raw_metadata,
                        "assessment": judgement.get("notes"),
                    }
                )
                round_trace.update(
                    {
                        "probe": probe,
                        "probe_type": probe_type,
                        "capability_id": capability_id,
                        "target_response": target_response.text,
                        "raw_metadata": raw_metadata,
                        "judgement_prompt": judgement_snapshot,
                        "judgement_response": judgement_response.text,
                        "judgement": judgement,
                    }
                )
                trace["rounds"].append(round_trace)

            for capability in report["capabilities"]:
                if capability["status"] == "claimed":
                    capability["status"] = "claimed_unverified"
            final_snapshot = await self._prompt_assets.render(
                "agent_recon.finalize.v1",
                {
                    "target_name": target_name,
                    "report": json.dumps(report, ensure_ascii=False),
                    "evidence": json.dumps(evidence, ensure_ascii=False),
                },
            )
            final_response = await generator.generate(Prompt(text=final_snapshot["rendered_text"]))
            final_report = _preserve_judged_evidence(
                report,
                _normalise_report(_extract_json(final_response.text)),
            )
            trace["final"] = {
                "prompt": final_snapshot,
                "response": final_response.text,
                "report": final_report,
            }
            trace_path = await self._write_trace(row.id, trace)
            async with self._sf() as session:
                saved = await session.get(TargetReconReport, row.id)
                saved.status = "succeeded"
                saved.report_json = final_report
                saved.trace_blob_path = trace_path
                await session.commit()
                await session.refresh(saved)
                return _public(saved)
        except Exception as exc:
            trace["error"] = f"{type(exc).__name__}: {exc}"
            trace_path = await self._write_trace(row.id, trace)
            async with self._sf() as session:
                saved = await session.get(TargetReconReport, row.id)
                saved.status = "failed"
                saved.error = trace["error"]
                saved.trace_blob_path = trace_path
                await session.commit()
                await session.refresh(saved)
                return _public(saved)
        finally:
            for obj in (target, generator):
                if obj is not None:
                    try:
                        await obj.aclose()
                    except Exception:
                        pass

    async def _write_trace(self, report_id: str, trace: dict[str, Any]) -> str:
        path = f"target-reconnaissance/{report_id}.json"
        await self._blob.put(path, json.dumps(trace, ensure_ascii=False).encode("utf-8"))
        return path
