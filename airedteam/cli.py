from __future__ import annotations
import asyncio
import json
import click


@click.group()
def main() -> None:
    """airedteam command-line interface."""


@main.command()
@click.option("--host", default="127.0.0.1")
@click.option("--port", default=8000, type=int)
def serve(host: str, port: int) -> None:
    """Run the FastAPI app with uvicorn."""
    import uvicorn
    from airedteam.api.app import create_app
    uvicorn.run(create_app(), host=host, port=port)


@main.command("run")
@click.argument("runspec_yaml", type=click.Path(exists=True))
@click.option("--name", default="cli-run")
def run_cmd(runspec_yaml: str, name: str) -> None:
    """Execute a RunSpec YAML file directly (uses default settings)."""
    import yaml
    from airedteam.api.deps import build_state
    state = build_state()

    async def _go():
        spec = yaml.safe_load(open(runspec_yaml).read())
        run = await state.runs.create_run(name=name, runspec_dict=spec)
        await state.runs.execute_run(run.id)
        click.echo(json.dumps({"run_id": run.id}))

@main.command("seed-datasets")
@click.option("--sample", is_flag=True, help="Seed the small smoke-test samples instead of full datasets.")
def seed_datasets(sample: bool) -> None:
    """Seed bundled AdvBench + HarmBench datasets into the DB."""
    from importlib import resources
    from airedteam.api.deps import build_state

    state = build_state()

    async def _go():
        samples = (
            [
                ("AdvBench (sample)", "advbench_sample.json"),
                ("HarmBench (sample)", "harmbench_sample.json"),
            ]
            if sample
            else [
                ("AdvBench", "advbench_full.json"),
                ("HarmBench", "harmbench_full.json"),
            ]
        )
        for name, filename in samples:
            data = resources.files("airedteam.builtins.datasets.samples").joinpath(filename).read_bytes()
            ds = await state.datasets.create_json_upload(name=name, file_bytes=data)
            click.echo(f"{name}: id={ds.id}  items={ds.item_count}")

    asyncio.run(_go())


if __name__ == "__main__":
    main()
