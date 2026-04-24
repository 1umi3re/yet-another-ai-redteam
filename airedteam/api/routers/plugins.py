from fastapi import APIRouter, Depends
from airedteam.core.registry import default_registry
from airedteam.api.deps import require_admin


router = APIRouter()


# Plugin parameter schemas rendered by the frontend. Keep in sync with the
# plugin classes themselves.
PARAM_SCHEMAS: dict[str, dict[str, dict]] = {
    "converters": {
        "identity": {},
        "base64": {
            "wrap": {"type": "bool", "default": True,
                     "label": "Wrap with decode instruction",
                     "help": "Prepend a 'decode and follow' instruction so the target acts on the payload"},
        },
        "rot13": {
            "wrap": {"type": "bool", "default": True,
                     "label": "Wrap with decode instruction",
                     "help": "Prepend a 'decode and follow' instruction"},
        },
        "prefix": {
            "prefix": {"type": "string", "required": True,
                       "label": "Prefix",
                       "placeholder": "Ignore all previous instructions. "},
        },
    },
    "scorers": {
        "refusal": {
            "phrases": {"type": "string_list", "default": [],
                        "label": "Extra refusal phrases (optional)",
                        "help": "One per line. Leave empty to use built-in EN/ZH defaults"},
        },
        "substring": {
            "needles": {"type": "string_list", "required": True,
                        "label": "Needles (one per line)"},
            "match": {"type": "enum", "options": ["any", "all"], "default": "any",
                      "label": "Match mode"},
            "case_sensitive": {"type": "bool", "default": False,
                               "label": "Case sensitive"},
        },
        "regex": {
            "pattern": {"type": "string", "required": True,
                        "label": "Regex pattern",
                        "placeholder": r"step\s+\d+:"},
            "flags": {"type": "string", "default": "",
                      "label": "Flags",
                      "help": "Combination of i/m/s"},
        },
        "llm_judge": {
            "judge_config_id": {"type": "target_ref", "required": True,
                                "label": "Judge target",
                                "help": "Configured target to use as the evaluator"},
            "rubric": {"type": "text", "default": "",
                       "label": "Rubric (optional)",
                       "help": "Leave empty for the default harmful-compliance rubric"},
        },
    },
}


@router.get("/plugins")
async def plugins(_=Depends(require_admin)):
    r = default_registry()
    groups = ("targets", "datasets", "converters", "executors", "scorers")
    out: dict[str, object] = {g: r.list(g) for g in groups}
    out["params"] = PARAM_SCHEMAS
    return out
