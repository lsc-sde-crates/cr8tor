import os
import typer
import asyncio
import cr8tor.core.api_client as api
import cr8tor.core.schema as schemas
import cr8tor.core.resourceops as project_resources
import cr8tor.core.crate_graph as proj_graph
import cr8tor.cli.utils as cli_utils

from pathlib import Path
from typing import Annotated, List, Tuple, Optional
from datetime import datetime

app = typer.Typer()


def merge_metadata_into_dataset(
    resource_path: Path, metadata: schemas.DatasetMetadata
) -> None:
    resource_data = project_resources.read_resource(resource_path)

    if "tables" not in resource_data:
        resource_data["tables"] = []

    table_lookup = {table["name"]: table for table in resource_data["tables"]}

    for meta_table in metadata.tables or []:
        if meta_table.name in table_lookup:
            existing_table = table_lookup[meta_table.name]
            existing_columns = existing_table.setdefault("columns", [])
            if meta_table.description:
                existing_table["description"] = meta_table.description

            existing_col_lookup = {col["name"]: col for col in existing_columns}

            for meta_col in meta_table.columns or []:
                if meta_col.name not in existing_col_lookup:
                    new_col = {"name": meta_col.name}
                    if meta_col.datatype:
                        new_col["datatype"] = meta_col.datatype
                    if meta_col.description:
                        new_col["description"] = meta_col.description
                    existing_columns.append(new_col)
                else:
                    existing_col = existing_col_lookup[meta_col.name]
                    if meta_col.description and "description" not in existing_col:
                        existing_col["description"] = meta_col.description
                    if meta_col.datatype and "datatype" not in existing_col:
                        existing_col["datatype"] = meta_col.datatype

        else:
            new_table = {"name": meta_table.name}
            if meta_table.columns:
                new_table["columns"] = []
                for col in meta_table.columns:
                    col_dict = {"name": col.name}
                    if col.datatype:
                        col_dict["datatype"] = col.datatype
                    if col.description:
                        col_dict["description"] = col.description
                    new_table["columns"].append(col_dict)

            resource_data["tables"].append(new_table)

    if metadata.description:
        resource_data["description"] = metadata.description

    project_resources.update_resource(resource_path, resource_data)


def verify_tables_metadata(
    remote_metadata: List[schemas.TableMetadata],
    local_metadata: List[schemas.TableMetadata],
) -> Tuple[bool, Optional[str]]:
    remote_lookup = {
        table.name: {col.name for col in table.columns} for table in remote_metadata
    }

    if local_metadata is not None:
        for local_table in local_metadata:
            table_name = local_table.name
            if table_name not in remote_lookup:
                return (
                    False,
                    f"Validation Error: Table '{table_name}' is missing from target schema metadata.",
                )

            remote_table_columns = remote_lookup[table_name]
            if local_table.columns is None:
                continue

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
        agent (str): The agent label triggering the validation. Defaults to None.
        bagit_dir (Path): The Bagit directory containing the RO-Crate data directory.
                          Defaults to "./bagit".
        resources_dir (Path): The directory containing resources to include in the RO-Crate.
                              Defaults to "./resources".

    This function performs the following:
    - Validates the contents of the specified Bagit directory and its RO-Crate data directory.
    - Validates access and governance metadata resources.
    - Rebuilds the Bagit contents, including the RO-Crate metadata.

    Example usage:
        cr8tor validate -b <path-to-bagit-dir> -i <path-to-resources-dir>
    """

    if agent is None:
        agent = os.getenv("AGENT_USER")

    exit_msg = "Validation complete"
    exit_code = schemas.Cr8torReturnCode.SUCCESS

    start_time = datetime.now()
    access_resource_path = resources_dir.joinpath("access", "access.toml")
    project_resource_path = resources_dir.joinpath("governance", "project.toml")
    project_dict = project_resources.read_resource_entity(
        project_resource_path, "project"
    )
    project_info = schemas.ProjectProps(**project_dict)

    current_rocrate_graph = proj_graph.ROCrateGraph(bagit_dir)
    if not current_rocrate_graph.is_project_action_complete(
        command_type=schemas.Cr8torCommandType.CREATE,
        action_type=schemas.RoCrateActionType.CREATE,
        project_id=project_info.id,
    ):
        cli_utils.close_assess_action_command(
            command_type=schemas.Cr8torCommandType.VALIDATE,
            start_time=start_time,
            project_id=project_info.id,
            agent=agent,
            project_resource_path=project_resource_path,
            resources_dir=resources_dir,
            exit_msg="The create command must be run on the target project before validation",
            exit_code=schemas.Cr8torReturnCode.ACTION_WORKFLOW_ERROR,
            instrument=os.getenv("METADATA_NAME"),
        )

    for dataset_meta_file in resources_dir.joinpath("metadata").glob("dataset_*.toml"):
        try:
            access = project_resources.read_resource(access_resource_path)
            dataset_meta = project_resources.read_resource(dataset_meta_file)
            source_data = {}
            source_data["source"] = access["source"].copy()
            source_data["source"]["type"] = source_data["source"]["type"].lower()
            source_data["source"]["credentials"] = access["credentials"]
            source_data["extract_config"] = (
                access["extract_config"] if "extract_config" in access else None
            )
            access_contract = schemas.DataContractValidateRequest(
                project_name=project_dict["project_name"],
                project_start_time=project_dict["project_start_time"],
                destination=project_dict["destination"],
                source=source_data["source"],
                extract_config=source_data.get("extract_config"),
                dataset=schemas.DatasetMetadata(**dataset_meta),
            )
            metadata = asyncio.run(api.validate_access(access_contract))
            validate_dataset_info = schemas.DatasetMetadata(**metadata)

        except Exception as e:
            cli_utils.close_assess_action_command(
                command_type=schemas.Cr8torCommandType.VALIDATE,
                start_time=start_time,
                project_id=project_info.id,
                agent=agent,
                project_resource_path=project_resource_path,
                resources_dir=resources_dir,
                exit_msg=f"{str(e)}",
                exit_code=schemas.Cr8torReturnCode.UNKNOWN_ERROR,
                instrument=os.getenv("METADATA_NAME"),
            )

        is_valid, err = verify_tables_metadata(
            validate_dataset_info.tables, access_contract.dataset.tables
        )
        if not is_valid:
            exit_msg = err
            exit_code = schemas.Cr8torReturnCode.VALIDATION_ERROR
            break

        merge_metadata_into_dataset(dataset_meta_file, validate_dataset_info)
    #
    # This assumes validate can be run multiple times on a project
    # Ensures previous run entities for this action are cleared in "actions" before
    # actions is updated with the new action entity
    #

    cli_utils.close_assess_action_command(
        command_type=schemas.Cr8torCommandType.VALIDATE,
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
