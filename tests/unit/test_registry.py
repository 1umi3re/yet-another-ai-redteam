def test_registry_loads_known_groups():
    from airedteam.core.registry import Registry
    r = Registry()
    assert "openai_compat" in r.list("targets")
    assert "anthropic_compat" in r.list("targets")
    assert "json_upload" in r.list("datasets")
    assert "hf" in r.list("datasets")
    assert {"identity", "base64", "rot13", "prefix"}.issubset(set(r.list("converters")))
    assert {"substring", "regex", "refusal", "llm_judge"}.issubset(set(r.list("scorers")))


def test_registry_get_returns_callable_class():
    from airedteam.core.registry import Registry
    r = Registry()
    cls = r.get("converters", "base64")
    inst = cls()
    assert inst.name == "base64"
