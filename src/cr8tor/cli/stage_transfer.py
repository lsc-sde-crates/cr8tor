import os
import typer
import asyncio
import uuid

from pathlib import Path
from typing import Annotated
from datetime import datetime

import cr8tor.core.api_client as api
import cr8tor.core.schema as schemas
import cr8tor.core.resourceops as project_resources
import cr8tor.core.crate_graph as proj_graph
import cr8tor.cli.utils as cli_utils


app = typer.Typer()


@app.command(name="stage-transfer")
def stage_transfer(
    agent: Annotated[
        str,
        typer.Option(default="-a", help="The agent label triggering the validation."),
    ] = None,
    bagit_dir: Annotated[
        Path,
        typer.Option(
            default="-b", help="Bagit directory containing RO-Crate data directory"
        ),
    ] = "./bagit",
    resources_dir: Annotated[
        Path,
        typer.Option(
            default="-i", help="Directory containing resources to include in RO-Crate."
        ),
    ] = "./resources",
):
    """
    Stages the data by transferring it from the specified source to sink TRE.

    Args:
        agent (str): The agent label triggering the validation. Defaults to None.
        bagit_dir (Path): Bagit directory containing RO-Crate data directory. Defaults to "./bagit".
        resources_dir (Path): Directory containing resources to include in RO-Crate. Defaults to "./resources".

    The function stages the data transfer for the specified CR8 project by validating the current RO-Crate graph
    and ensuring that the necessary resources are included.

    Example usage:

        cr8tor stage-transfer -a agent_label -b path-to-bagit-dir -i path-to-resources-dir
    """

    if agent is None:
        agent = os.getenv("AGENT_USER")

    exit_msg = "Staging transfer complete"
    exit_code = schemas.Cr8torReturnCode.SUCCESS
    staging_results = []
    start_time = datetime.now()

    project_resource_path = resources_dir.joinpath("governance", "project.toml")
    access_resource_path = resources_dir.joinpath("access", "access.toml")
    project_info = project_resources.read_resource(project_resource_path)

    if not bagit_dir.exists():
        cli_utils.exit_command(
            schemas.Cr8torCommandType.DISCLOSURE_CHECK,
            schemas.Cr8torReturnCode.ACTION_EXECUTION_ERROR,
            f"Missing bagit directory at: {bagit_dir}",
        )

    current_rocrate_graph = proj_graph.ROCrateGraph(bagit_dir)

    if not current_rocrate_graph.is_project_action_complete(
        command_type=schemas.Cr8torCommandType.SIGN_OFF,
        action_type=schemas.RoCrateActionType.ASSESS,
        project_id=project_info["project"]["id"],
    ):
        cli_utils.close_create_action_command(
            command_type=schemas.Cr8torCommandType.STAGE_TRANSFER,
            start_time=start_time,
            project_id=project_info["project"]["id"],
            agent=agent,
            project_resource_path=project_resource_path,
            resources_dir=resources_dir,
            exit_msg="The data project must have sign-off before staging the data transfer",
            exit_code=schemas.Cr8torReturnCode.ACTION_WORKFLOW_ERROR,
            instrument=os.getenv("PUBLISH_NAME"),
        )

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
        except Exception as e:
            cli_utils.close_create_action_command(
                command_type=schemas.Cr8torCommandType.STAGE_TRANSFER,
                start_time=start_time,
                project_id={project_info["project"]["id"]},
                agent=agent,
                project_resource_path=project_resource_path,
                resources_dir=resources_dir,
                exit_msg=f"{str(e)}",
                exit_code=schemas.Cr8torReturnCode.UNKNOWN_ERROR,
                instrument=os.getenv("PUBLISH_NAME"),
            )

        resp_dict = asyncio.run(api.stage_transfer(access_contract))
        validate_resp = schemas.StageTransferPayload(**resp_dict)

        # TODO: Handle multiple staging locations
        # TODO: Add error response handler for action error property

        if validate_resp.data_retrieved and validate_resp.data_retrieved[0].file_path:
            staging_location_dict = validate_resp.data_retrieved[0].model_dump()
            staging_location_dict["@id"] = str(uuid.uuid4())

            staging_results.append(staging_location_dict)

            project_resources.create_resource_entity(
                dataset_meta_file, "staging_path", staging_location_dict
            )

    cli_utils.close_create_action_command(
        command_type=schemas.Cr8torCommandType.STAGE_TRANSFER,
        start_time=start_time,
        project_id=project_info["project"]["id"],
        agent=agent,
        project_resource_path=project_resource_path,
        resources_dir=resources_dir,
        exit_msg=exit_msg,
        exit_code=exit_code,
        instrument=os.getenv("PUBLISH_NAME"),
        result=staging_results,
    )

    # if staging_results:
    #     status = schemas.ActionStatusType.COMPLETED
    # else:
    #     # TODO: Is no path in response for datasets a failure?
    #     status = schemas.ActionStatusType.FAILED

    # create_transfer_action_props = schemas.CreateActionProps(
    #     id=f"stage-transfer-action-{project_info['project']['id']}",
    #     name="Stage Data Transfer Action",
    #     start_time=start_time,
    #     end_time=datetime.now(),
    #     action_status=status,
    #     agent=agent,
    #     error=None,
    #     instrument=os.getenv("PUBLISH_NAME"),
    #     result=staging_results,
    # )

    # project_resources.delete_resource_entity(
    #     project_resource_path,
    #     "actions",
    #     "id",
    #     f"stage-transfer-action-{project_info['project']['id']}",
    # )
    # project_resources.update_resource_entity(
    #     project_resource_path, "actions", create_transfer_action_props.model_dump()
    # )

    # ro_crate_builder.build(resources_dir)
