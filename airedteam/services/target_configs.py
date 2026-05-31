from __future__ import annotations

from sqlalchemy import select

from airedteam.storage.models import TargetConfig
from airedteam.storage.secretbox import SecretBox


class TargetConfigService:
    def __init__(self, session_factory, secret_box: SecretBox) -> None:
        self._sf = session_factory
        self._box = secret_box

    async def create(self, *, name: str, plugin: str, params: dict, secret: dict | None = None) -> TargetConfig:
        async with self._sf() as s:
            ct = self._box.encrypt(secret) if secret else None
            row = TargetConfig(name=name, plugin=plugin, params_json=params, secret_ciphertext=ct)
            s.add(row)
            await s.commit()
            await s.refresh(row)
            return row

    async def list(self) -> list[TargetConfig]:
        async with self._sf() as s:
            r = await s.execute(select(TargetConfig).order_by(TargetConfig.created_at.desc()))
            return list(r.scalars().all())

    async def get(self, cfg_id: str) -> TargetConfig | None:
        async with self._sf() as s:
            return await s.get(TargetConfig, cfg_id)

    async def delete(self, cfg_id: str) -> None:
        async with self._sf() as s:
            row = await s.get(TargetConfig, cfg_id)
            if row:
                await s.delete(row)
                await s.commit()

    async def update_limits(
        self,
        cfg_id: str,
        *,
        timeout_set: bool = False,
        timeout: float | None = None,
        max_concurrency_set: bool = False,
        max_concurrency: int | None = None,
        max_input_chars_set: bool = False,
        max_input_chars: int | None = None,
        input_limit_unit_set: bool = False,
        input_limit_unit: str | None = None,
    ) -> TargetConfig:
        async with self._sf() as s:
            row = await s.get(TargetConfig, cfg_id)
            if row is None:
                raise KeyError(cfg_id)
            params = dict(row.params_json or {})
            if timeout_set:
                if timeout is None:
                    params.pop("timeout", None)
                else:
                    params["timeout"] = timeout
            if max_concurrency_set:
                if max_concurrency is None:
                    params.pop("max_concurrency", None)
                else:
                    params["max_concurrency"] = max_concurrency
            if max_input_chars_set:
                if max_input_chars is None:
                    params.pop("max_input_chars", None)
                else:
                    params["max_input_chars"] = max_input_chars
            if input_limit_unit_set:
                if input_limit_unit is None:
                    params.pop("input_limit_unit", None)
                else:
                    params["input_limit_unit"] = input_limit_unit
            row.params_json = params
            await s.commit()
            await s.refresh(row)
            return row

    async def resolve_for_runtime(self, cfg_id: str) -> dict:
        cfg = await self.get(cfg_id)
        if cfg is None:
            raise KeyError(cfg_id)
        params = dict(cfg.params_json or {})
        if cfg.secret_ciphertext:
            params.update(self._box.decrypt(cfg.secret_ciphertext))
        return {"plugin": cfg.plugin, "params": params}
