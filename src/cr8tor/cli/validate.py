import os
import typer
import asyncio
import cr8tor.core.api_client as api
import cr8tor.core.schema as s
import cr8tor.core.resourceops as project_resources
import cr8tor.core.crate_graph as proj_graph
import cr8tor.cli.utils as cli_utils

from pathlib import Path
from typing import Annotated, List, Tuple, Optional
from datetime import datetime

app = typer.Typer()


def verify_tables_metadata(
    remote_metadata: List[s.TableMetadata], local_metadata: List[s.TableMetadata]
) -> Tuple[bool, Optional[str]]:
    remote_lookup = {
        table.name: {col.name for col in table.columns} for table in remote_metadata
    }

    for local_table in local_metadata:
        table_name = local_table.name
        if table_name not in remote_lookup:
            return (
                False,
                f"Validation Error: Table '{table_name}' is missing from target schema metadata.",
            )

        remote_table_columns = remote_lookup[table_name]
        for filter_col in local_table.columns:
            if filter_col.name not in remote_table_columns:
                return (
                    False,
                    f"Validation Error: Column '{filter_col.name}' is missing from target schema table '{table_name}' metadata.",
                )

    return True, None


@app.command(name="validate")
def validate(
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
    Validate the contents of a Bagit directory containing an RO-Crate data directory.

    Args:
        bag_dir (Path): The Bagit directory containing the RO-Crate data directory.
                        Defaults to "./bagit".
        resources_dir (Path): The directory containing resources to include in the RO-Crate.
                              Defaults to "./resources".

    The function validates the contents of the specified access and governance metadata resources and rebuilds the
    Bagit contents including the RO-Crate metadata.

    Example usage:

        cr8tor validate -b path-to-bagit-dir -i path-to-resources-dir

    """

    if agent is None:
        agent = os.getenv("AGENT_USER")

    exit_msg = "Validation complete"
    exit_code = s.Cr8torReturnCode.SUCCESS

    start_time = datetime.now()
    access_resource_path = resources_dir.joinpath("access", "access.toml")
    project_resource_path = resources_dir.joinpath("governance", "project.toml")
    project_dict = project_resources.read_resource_entity(
        project_resource_path, "project"
    )
    project_info = s.ProjectProps(**project_dict)

    current_rocrate_graph = proj_graph.ROCrateGraph(bagit_dir)
    if not current_rocrate_graph.is_created():
        cli_utils.close_assess_action_command(
            command_type=s.Cr8torCommandType.VALIDATE,
            start_time=start_time,
            project_id=project_info.id,
            agent=agent,
            project_resource_path=project_resource_path,
            resources_dir=resources_dir,
            exit_msg="The create command must be run on the target project before validation",
            exit_code=s.Cr8torReturnCode.ACTION_WORKFLOW_ERROR,
            instrument=os.getenv("METADATA_NAME"),
        )

    for dataset_meta_file in resources_dir.joinpath("metadata").glob("dataset_*.toml"):
        try:
            access = project_resources.read_resource(access_resource_path)
            dataset_meta = project_resources.read_resource(dataset_meta_file)
            access_contract = s.DataContractValidateRequest(
                source=s.DatabricksSourceConnection(**access["source"]),
                credentials=s.SourceAccessCredential(**access["credentials"]),
                # TODO: Validate & select against porject pydantic model
                project_name=project_dict["project_name"],
                project_start_time=project_dict["project_start_time"],
                destination_type=project_dict["destination_type"],
                destination_format=project_dict["destination_format"],
                dataset=s.DatasetMetadata(**dataset_meta),
            )
        except Exception as e:
            cli_utils.close_assess_action_command(
                command_type=s.Cr8torCommandType.VALIDATE,
                start_time=start_time,
                project_id=project_info.id,
                agent=agent,
                project_resource_path=project_resource_path,
                resources_dir=resources_dir,
                exit_msg=f"{str(e)}",
                exit_code=s.Cr8torReturnCode.UNKNOWN_ERROR,
                instrument=os.getenv("METADATA_NAME"),
            )

        metadata = asyncio.run(api.validate_access(access_contract))
        validate_dataset_info = s.DatasetMetadata(**metadata)

        is_valid, err = verify_tables_metadata(
            validate_dataset_info.tables, access_contract.dataset.tables
        )
        if not is_valid:
            exit_msg = err
            exit_code = s.Cr8torReturnCode.VALIDATION_ERROR
            break

    #
    # This assumes validate can be run multiple times on a project
    # Ensures previous run entities for this action are cleared in "actions" before
    # actions is updated with the new action entity
    #

    cli_utils.close_assess_action_command(
        command_type=s.Cr8torCommandType.VALIDATE,
        start_time=start_time,
        project_id=project_info.id,
        agent=agent,
        project_resource_path=project_resource_path,
        resources_dir=resources_dir,
        exit_msg=exit_msg,
        exit_code=exit_code,
        instrument=os.getenv("METADATA_NAME"),
        additional_type="Semantic Validation",
    )
