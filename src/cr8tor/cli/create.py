import os
import uuid
import typer
import cr8tor.core.schema as schemas

from pathlib import Path
from typing import Annotated
from datetime import datetime
import cr8tor.core.resourceops as project_resources
import cr8tor.cli.build as ro_crate_builder
import cr8tor.core.crate_graph as proj_graph

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
    Create generates the initial RO-Crate data crate within the target Cr8tor project from the specified metadata resources.
    This function generates a uuid for the project and then builds a RO-Crate along with RO-Crate knowledge graph which is further packaged
    as a non-serialised BagIt Archive in the "bagit/" directory. If the `dryrun` argument is provided, the function will print the crate
    details without writing to the "crate/" directory.

    Args:
        agent (str): The agent label triggering the validation. Defaults to None.
        resources_dir (Path): Directory containing resources to include in RO-Crate. Defaults to "./resources".
        bagit_dir (Path): Bagit directory containing RO-Crate data directory. Defaults to "./bagit".
        config_file (Path): Location of configuration TOML file. Defaults to "./config.toml".
        dryrun (bool): If provided, the function will print the crate details without writing to the "crate/" directory. Defaults to False.

    Example usage:

        cr8tor create -a agent_label -i path-to-resources-dir -b path-to-bagit-dir -c path-to-config-file --dryrun

    """

    if agent is None:
        agent = os.getenv("APP_NAME")

    create_start_dt = datetime.now()
    project_uuid: Annotated[
        str,
        "Project UUID is a unique auto-generated identifier on creation of the project",
    ] = os.getenv("PROJECT_UUID", str(uuid.uuid4()))

    if not resources_dir.exists():
        typer.echo(f"Missing resrouces directory at: {resources_dir}", err=True)
        raise typer.Exit(code=1)

    project_resource_path = resources_dir.joinpath("governance", "project.toml")
    governance = project_resources.read_resource(project_resource_path)

    if bagit_dir.exists():
        current_rocrate_graph = proj_graph.ROCrateGraph(bagit_dir)

        if current_rocrate_graph.is_created() and "id" in governance["project"]:
            typer.echo(
                f"A create action has already been run on this project. Project ID: {governance['project']['id']}",
                err=True,
            )
            raise typer.Exit(code=1)

    governance["project"].setdefault("id", project_uuid)
    governance["project"].setdefault(
        "project_start_time", create_start_dt.strftime("%Y%m%d_%H%M%S")
    )
    project_resources.update_resource_entity(
        project_resource_path, "project", governance["project"]
    )

    create_action_props = schemas.CreateActionProps(
        id=f"create-project-action-{project_uuid}",
        name="Create LSC Project Action",
        start_time=create_start_dt,
        end_time=datetime.now(),
        action_status=schemas.ActionStatusType.COMPLETED,
        agent=agent,
        error=None,
        instrument="cr8tor",
        result=[{"@id": project_uuid}],
    )

    project_resources.create_resource_entity(project_resource_path, "actions", [])
    project_resources.update_resource_entity(
        project_resource_path, "actions", create_action_props.model_dump()
    )

    ro_crate_builder.build(resources_dir, config_file, dryrun)
