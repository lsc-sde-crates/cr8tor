import typer
from pathlib import Path
from typing import Annotated

# from cr8tor.core.resourceops import *
from cr8tor.cli.app import app
import cr8tor.cli.build as ro_crate_builder


@app.command(name="publish")
def publish(
    agent: Annotated[
        str,
        typer.Option(default="-a", help="The agent label triggering the validation."),
    ] = None,
    bagit_dir: Annotated[
        Path,
        typer.Option(
            default="-i", help="Bagit directory containing RO-Crate data directory"
        ),
    ] = "./bagit",
    resources_dir: Annotated[
        Path,
        typer.Option(
            default="-i", help="Directory containing resources to include in RO-Crate."
        ),
    ] = "./resources",
    agent_token: Annotated[
        str,
        typer.Option(default="-i", help=""),
    ] = "./resources",
):
    # project_resource_path = resources_dir.joinpath("governance", "project.toml")
    # proj_roc_meta_path = bagit_dir.joinpath("data")

    #
    # Log the action and update on statuses
    #

    ro_crate_builder.build(resources_dir)
