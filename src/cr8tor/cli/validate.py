import os
import typer
import asyncio
import cr8tor.core.api_client as api
import cr8tor.core.schema as s
import cr8tor.cli.build as ro_crate_builder
import cr8tor.core.resourceops as project_resources

from pathlib import Path
from typing import Annotated, List, Tuple, Optional
from datetime import datetime
from pydantic import ValidationError

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
            default="-i", help="Bagit directory containing RO-Crate data directory"
        ),
    ] = "./bagit",
    resources_dir: Annotated[
        Path,
        typer.Option(
            default="-i", help="Directory containing resources to include in RO-Crate."
        ),
    ] = "./resources",
):
    if agent is None:
        agent = os.getenv("APP_NAME")

    start_time = datetime.now()
    # proj_roc_meta_path = bagit_dir.joinpath("data")
    access_resource_path = resources_dir.joinpath("access", "access.toml")
    project_resource_path = resources_dir.joinpath("governance", "project.toml")
    project_dict = project_resources.read_resource_entity(
        project_resource_path, "project"
    )
    project_info = s.ProjectProps(**project_dict)

    #
    # Check if create actions are complete in knowledge graph
    #
    # graph = ROCrateGraph(crate_meta_file)
    # if not graph.is_created():
    #     raise Exception(
    #         "Cannot perform this action becase ro-crate has not completed creation phase"
    #     )

    is_valid = True

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
        except ValidationError as e:
            print("Validation Error:", e)

        except Exception as e:
            print("An unexpected error occurred:", e)

        metadata = asyncio.run(api.validate_access(access_contract, True))
        validate_dataset_info = s.DatasetMetadata(**metadata)

        is_valid, err = verify_tables_metadata(
            validate_dataset_info.tables, access_contract.dataset.tables
        )
        if not is_valid:
            break

    #
    # Check if performed and/or status of validate action on project in metatdata knowledge graph
    #
    # if doesnt exist, create action and set status
    #

    statusType = s.ActionStatusType.COMPLETED if is_valid else s.ActionStatusType.FAILED

    assess_action_props = s.AssessActionProps(
        id=f"validate-sem-{project_info.id}",
        name="Validate action",
        start_time=start_time,
        end_time=datetime.now(),
        action_status=statusType,
        agent=agent,
        error=err,
        instrument=os.getenv("METADATA_NAME"),
        additional_type="Semantic Validation",
    )

    project_resources.update_resource_entity(
        project_resource_path, "actions", assess_action_props.model_dump()
    )

    #
    # If exists update status
    #

    ro_crate_builder.build(resources_dir)
