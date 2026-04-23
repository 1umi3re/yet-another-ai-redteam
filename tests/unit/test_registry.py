from airedteam.core.registry import Registry


def test_registry_loads_known_groups():
    r = Registry()
    assert isinstance(r.list("targets"), list)
    assert isinstance(r.list("converters"), list)
