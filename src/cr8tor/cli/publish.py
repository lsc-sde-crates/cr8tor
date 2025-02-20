import os
import typer
# import asyncio

from pathlib import Path
from typing import Annotated

# import cr8tor.core.api_client as api
import cr8tor.cli.build as ro_crate_builder

app = typer.Typer()


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
    if agent is None:
        agent = os.getenv("APP_NAME")

    # resp_dict = asyncio.run(api.stage_transfer(None, True))
    # print(resp_dict)
    ro_crate_builder.build(resources_dir)
