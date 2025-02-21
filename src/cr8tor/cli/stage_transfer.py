import os
import typer
import asyncio

from pathlib import Path
from typing import Annotated
from datetime import datetime
from pydantic import ValidationError

import cr8tor.core.api_client as api
import cr8tor.core.schema as schemas
import cr8tor.core.resourceops as project_resources
import cr8tor.cli.build as ro_crate_builder

app = typer.Typer()


@app.command(name="stage-transfer")
def stage_transfer(
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
):
    if agent is None:
        agent = os.getenv("APP_NAME")

    project_resource_path = resources_dir.joinpath("governance", "project.toml")
    access_resource_path = resources_dir.joinpath("access", "access.toml")
    project_info = project_resources.read_resource(project_resource_path)
    # crate_meta_file = bagit_dir.joinpath("data", "ro-crate-metadata.json")

    #
    # Check if create & validate, approvals actions are complete in knowledge graph
    #
    # graph = ROCrateGraph(crate_meta_file)
    # if not graph.is_validated():
    #     raise Exception(
    #         "Cannot perform this action becase ro-crate has not completed validation phase"
    #     )

    staging_results = []
    status = schemas.ActionStatusType.ACTIVE
    start_time = datetime.now()

    for dataset_meta_file in resources_dir.joinpath("metadata").glob("dataset*.toml"):
        dataset_dict = project_resources.read_resource(dataset_meta_file)
        dataset_props = schemas.DatasetMetadata(**dataset_dict)

        try:
            access = project_resources.read_resource(access_resource_path)
            access_contract = schemas.DataContractStageTransferRequest(
                source=schemas.DatabricksSourceConnection(**access["source"]),
                credentials=schemas.SourceAccessCredential(**access["credentials"]),
                # TODO: Validate & select against porject pydantic model
                project_name=project_info["project"]["project_name"],
                project_start_time=project_info["project"]["project_start_time"],
                destination_type=project_info["project"]["destination_type"],
                destination_format=project_info["project"]["destination_format"],
                metadata=dataset_props,
            )
        except ValidationError as e:
            print("Validation Error:", e)

        except Exception as e:
            print("An unexpected error occurred:", e)

        resp_dict = asyncio.run(api.stage_transfer(access_contract, True))
        validate_resp = schemas.HTTPPayloadResponse(**resp_dict)

        # TODO: Handle multiple staging locations
        # TODO: Add error response handler for action error property

        if (
            validate_resp.payload.data_retrieved
            and validate_resp.payload.data_retrieved[0].file_path
        ):
            staging_location_dict = validate_resp.payload.data_retrieved[0].model_dump()

            staging_results.append(staging_location_dict)

            project_resources.create_resource_entity(
                dataset_meta_file, "staging_path", staging_location_dict["file_path"]
            )

    if staging_results:
        status = schemas.ActionStatusType.COMPLETED
    else:
        # TODO: Is no path in response for datasets a failure?
        status = schemas.ActionStatusType.FAILED

    create_transfer_action_props = schemas.CreateActionProps(
        id=f"stage-transfer-action-{project_info['project']['id']}",
        name="Create LSC Project Action",
        start_time=start_time,
        end_time=datetime.now(),
        action_status=status,
        agent=agent,
        error=None,
        instrument=os.getenv("PUBLISH_NAME"),
        result=staging_results,
    )

    project_resources.update_resource_entity(
        project_resource_path, "actions", create_transfer_action_props.model_dump()
    )

    ro_crate_builder.build(resources_dir)
