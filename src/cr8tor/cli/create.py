import os
import uuid
import typer
import cr8tor.core.schema as schemas

from pathlib import Path
from typing import Annotated
from datetime import datetime
import cr8tor.core.resourceops as project_resources
import cr8tor.core.crate_graph as proj_graph
import cr8tor.cli.utils as cli_utils

app = typer.Typer()


@app.command(name="create")
def create(
    agent: Annotated[
        str,
        typer.Option(default="-a", help="The agent label triggering the validation."),
    ] = None,
    resources_dir: Annotated[
        Path,
        typer.Option(
            default="-i", help="Directory containing resources to include in RO-Crate."
        ),
    ] = "./resources",
    bagit_dir: Annotated[
        Path,
        typer.Option(
            default="-b", help="Bagit directory containing RO-Crate data directory"
        ),
    ] = "./bagit",
    config_file: Annotated[
        Path, typer.Option(default="-c", help="Location of configuration TOML file.")
    ] = "./config.toml",
    dryrun: Annotated[bool, typer.Option(default="--dryrun")] = False,
):
    """
    Generates the initial RO-Crate data crate within the target Cr8tor project from the specified metadata resources.

    This command performs the following actions:
    - Generates a UUID for the project.
    - Builds an RO-Crate along with an RO-Crate knowledge graph.
    - Packages the crate as a non-serialized BagIt Archive in the "bagit/" directory.
    - If the `dryrun` option is provided, prints the crate details without writing to the "crate/" directory.

    Args:
        agent (str): The agent label triggering the validation. Defaults to None.
        resources_dir (Path): Directory containing resources to include in the RO-Crate. Defaults to "./resources".
        bagit_dir (Path): Bagit directory containing the RO-Crate data directory. Defaults to "./bagit".
        config_file (Path): Location of the configuration TOML file. Defaults to "./config.toml".
        dryrun (bool): If True, prints the crate details without writing to the "crate/" directory. Defaults to False.

    Example usage:
        cr8tor create -a agent_label -i path-to-resources-dir -b path-to-bagit-dir -c path-to-config-file --dryrun
    """

    if agent is None:
        agent = os.getenv("AGENT_USER")

    exit_msg = "Create complete"
    exit_code = schemas.Cr8torReturnCode.SUCCESS

    create_start_dt = datetime.now()
    project_uuid: Annotated[
        str,
        "Project UUID is a unique auto-generated identifier on creation of the project",
    ] = os.getenv("PROJECT_UUID", str(uuid.uuid4()))

    if not resources_dir.exists():
        cli_utils.exit_command(
            schemas.Cr8torCommandType.CREATE,
            schemas.Cr8torReturnCode.ACTION_EXECUTION_ERROR,
            f"Missing resources directory at: {resources_dir}",
        )

    project_resource_path = resources_dir.joinpath("governance", "project.toml")
    governance = project_resources.read_resource(project_resource_path)

    if bagit_dir.exists():
        if "id" in governance["project"]:
            current_rocrate_graph = proj_graph.ROCrateGraph(bagit_dir)
            if current_rocrate_graph.is_project_action_complete(
                command_type=schemas.Cr8torCommandType.CREATE,
                action_type=schemas.RoCrateActionType.CREATE,
                project_id=governance["project"]["id"],
            ):
                cli_utils.exit_command(
                    schemas.Cr8torCommandType.CREATE,
                    schemas.Cr8torReturnCode.ACTION_EXECUTION_ERROR,
                    "Create command can only be run once on a project",
                )

    governance["project"].setdefault("id", project_uuid)
    governance["project"].setdefault(
        "project_start_time", create_start_dt.strftime("%Y%m%d_%H%M%S")
    )
    project_resources.update_resource_entity(
        project_resource_path, "project", governance["project"]
    )

    project_resources.create_resource_entity(project_resource_path, "actions", [])

    cli_utils.close_create_action_command(
        command_type=schemas.Cr8torCommandType.CREATE,
        start_time=create_start_dt,
        project_id=project_uuid,
        agent=agent,
        project_resource_path=project_resource_path,
        resources_dir=resources_dir,
        exit_msg=exit_msg,
        exit_code=exit_code,
        instrument=os.getenv("APP_NAME"),
        result=[{"@id": project_uuid}],
        dryrun=dryrun,
        config_file=config_file,
    )
