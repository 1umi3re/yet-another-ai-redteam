import json
from importlib import resources


def _fixture(name: str) -> dict:
    raw = resources.files("airedteam.builtins.datasets.samples").joinpath(name).read_text()
    return json.loads(raw)


def test_advbench_full_fixture_schema():
    data = _fixture("advbench_full.json")
    items = data["items"]
    assert len(items) == 520
    assert all(item["id"].startswith("advbench-") for item in items)
    assert all(item["prompt"] for item in items)
    assert all(item["source"] == "advbench" for item in items)


def test_harmbench_full_fixture_schema():
    data = _fixture("harmbench_full.json")
    items = data["items"]
    assert len(items) == 400
    assert all(item["id"] for item in items)
    assert all(item["prompt"] for item in items)
    assert all(item["source"] == "harmbench" for item in items)
    assert all("semantic_category" in item for item in items)
