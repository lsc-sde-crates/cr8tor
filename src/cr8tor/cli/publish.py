import os
import typer
import asyncio

from pathlib import Path
from typing import Annotated
import cr8tor.core.schema as schemas
import cr8tor.core.resourceops as project_resources

from datetime import datetime

import cr8tor.core.api_client as api
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
        typer.Option(
            default="-a", help="Auth token for the agent triggering publish action."
        ),
    ] = None,
):
    if agent is None:
        agent = os.getenv("APP_NAME")

    publish_results = []
    err = ""
    status = schemas.ActionStatusType.ACTIVE
    start_time = datetime.now()

    project_resource_path = resources_dir.joinpath("governance", "project.toml")
    project_info = project_resources.read_resource(project_resource_path)

    dataset_meta_file = None

    # TODO: Discuss with Piotr whether the publish function should be called per dataset or per project?
    # Currently assumes 1 dataset file in metadata

    for f in resources_dir.joinpath("metadata").glob("dataset*.toml"):
        dataset_meta_file = f
        break

    publish_req = schemas.DataContractProjectRequest(
        project_name=project_info["project"]["project_name"],
        project_start_time=project_info["project"]["project_start_time"],
        destination_type=project_info["project"]["destination_type"],
    )

    resp_dict = asyncio.run(api.publish(publish_req, True))
    validate_resp = schemas.HTTPPayloadResponse(**resp_dict)

    if (
        validate_resp.payload.data_published
        and validate_resp.payload.data_published[0].file_path
    ):
        publish_location_dict = validate_resp.payload.data_published[0].model_dump()
        publish_results.append(publish_location_dict)

        project_resources.create_resource_entity(
            dataset_meta_file, "publish_path", publish_location_dict["file_path"]
        )

    if publish_results:
        status = schemas.ActionStatusType.COMPLETED
    else:
        # TODO: Is no path in response for datasets a failure?
        status = schemas.ActionStatusType.FAILED
        err = "No result"

    create_publish_action_props = schemas.CreateActionProps(
        id=f"publish-action-{project_info['project']['id']}",
        name="Create LSC Project Action",
        start_time=start_time,
        end_time=datetime.now(),
        action_status=status,
        agent=agent,
        error=err,
        instrument=os.getenv("PUBLISH_NAME"),
        result=publish_results,
    )

    project_resources.update_resource_entity(
        project_resource_path, "actions", create_publish_action_props.model_dump()
    )

    ro_crate_builder.build(resources_dir)
