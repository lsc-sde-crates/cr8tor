import os
import typer
import asyncio
import cr8tor.core.api_client as api
import cr8tor.core.schema as s
import cr8tor.cli.build as ro_crate_builder
import cr8tor.core.resourceops as project_resources
import cr8tor.core.crate_graph as proj_graph

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
        agent = os.getenv("APP_NAME")

    exit_msg = "Validation complete"
    exit_code = s.Cr8torErrorCode.SUCCESS

    start_time = datetime.now()
    access_resource_path = resources_dir.joinpath("access", "access.toml")
    project_resource_path = resources_dir.joinpath("governance", "project.toml")
    project_dict = project_resources.read_resource_entity(
        project_resource_path, "project"
    )
    project_info = s.ProjectProps(**project_dict)

    current_rocrate_graph = proj_graph.ROCrateGraph(bagit_dir)
    if not current_rocrate_graph.is_created():
        close_command(
            start_time,
            project_info,
            agent,
            project_resource_path,
            resources_dir,
            "Error: The create command must be run on the target project before validation",
            s.Cr8torErrorCode.INCOMPLETE_ACTION_ERROR,
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
            close_command(
                start_time,
                project_info,
                agent,
                project_resource_path,
                resources_dir,
                f"Error: {str(e)}",
                s.Cr8torErrorCode.UNKNOWN_ERROR,
            )

        metadata = asyncio.run(api.validate_access(access_contract))
        validate_dataset_info = s.DatasetMetadata(**metadata)

        is_valid, err = verify_tables_metadata(
            validate_dataset_info.tables, access_contract.dataset.tables
        )
        if not is_valid:
            exit_msg = err
            exit_code = s.Cr8torErrorCode.VALIDATION_ERROR
            break

    close_command(
        start_time,
        project_info,
        agent,
        project_resource_path,
        resources_dir,
        exit_msg,
        exit_code,
    )


def close_command(
    start_time: datetime,
    project_info: s.ProjectProps,
    agent: str,
    project_resource_path: Path,
    resources_dir: Path,
    exit_msg: str,
    exit_code: int,
):
    if exit_code == s.Cr8torErrorCode.SUCCESS:
        status_type = s.ActionStatusType.COMPLETED
        err = None
    else:
        status_type = s.ActionStatusType.FAILED
        err = exit_msg

    assess_action_props = s.AssessActionProps(
        id=f"validate-sem-{project_info.id}",
        name="Validate LSC Project Action",
        start_time=start_time,
        end_time=datetime.now(),
        action_status=status_type,
        agent=agent,
        error=err,
        instrument=os.getenv("METADATA_NAME"),
        additional_type="Semantic Validation",
        result=[],
    )

    #
    # This assumes validate can be run multiple times on a project
    # Ensures previous run entities for this action are cleared in "actions" before
    # actions is updated with the new action entity
    #

    project_resources.delete_resource_entity(
        project_resource_path, "actions", "id", f"validate-sem-{project_info.id}"
    )
    project_resources.update_resource_entity(
        project_resource_path, "actions", assess_action_props.model_dump()
    )

    ro_crate_builder.build(resources_dir)

    if exit_code == s.Cr8torErrorCode.SUCCESS:
        typer.echo("Validation completed successfully")
    else:
        typer.echo(
            f"Validation failed with error code {exit_code}: {exit_msg}", err=True
        )
        raise typer.Exit(code=exit_code)
