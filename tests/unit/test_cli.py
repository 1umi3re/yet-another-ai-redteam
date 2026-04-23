from click.testing import CliRunner
from airedteam.cli import main


def test_help_lists_commands():
    r = CliRunner().invoke(main, ["--help"])
    assert r.exit_code == 0
    assert "serve" in r.output
    assert "run" in r.output
