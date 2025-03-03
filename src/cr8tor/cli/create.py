import os
import uuid
import typer
import cr8tor.core.schema as schemas

from pathlib import Path
from typing import Annotated
from datetime import datetime
from cr8tor.exception import DirectoryNotFoundError
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
            default="-i", help="Bagit directory containing RO-Crate data directory"
        ),
    ] = "./bagit",
    config_file: Annotated[
        Path, typer.Option(default="-c", help="Location of configuration TOML file.")
    ] = "./config.toml",
    dryrun: Annotated[bool, typer.Option(default="--dryrun")] = False,
):
    """
    Create initialises a 5-Safes Research Object Crate (RO-Crate) from specified metadata resources.
    This function generates a uuid for the project and then builds a RO-Crate along with knowledge graph which is then packaged
    as a BagIt Archive in the "bagit/" directory. If the `dryrun` argument is provided, the function will print the crate
    details without writing to the "crate/" directory.

    Example:
        $ cr8tor create -a GithubAction -i /path/to/resources
    """

    if agent is None:
        agent = os.getenv("APP_NAME")

    create_start_dt = datetime.now()
    project_uuid: Annotated[
        str,
        "Project UUID is a unique auto-generated identifier on creation of the project",
    ] = os.getenv("PROJECT_UUID", str(uuid.uuid4()))

    if not resources_dir.exists():
        raise DirectoryNotFoundError(resources_dir)

    project_resource_path = resources_dir.joinpath("governance", "project.toml")

    proj_roc_meta_path = bagit_dir.joinpath("data", "ro-crate-metadata.json")
    governance = project_resources.read_resource(project_resource_path)

    graph = proj_graph.ROCrateGraph(proj_roc_meta_path)

    if graph.is_created() and "id" in governance["project"]:
        print(
            f"A create action has already been run on this project. Project ID: {governance['project']['id']}"
        )
        return

    governance["project"].setdefault("id", project_uuid)
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
        project_resource_path, "actions", create_action_props.dict()
    )

    ro_crate_builder.build(resources_dir, config_file, dryrun)
