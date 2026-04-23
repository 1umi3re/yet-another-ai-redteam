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

    asyncio.run(_go())
