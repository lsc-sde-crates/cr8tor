import typer
import cr8tor.core.schema as schemas
import cr8tor.cli.build as ro_crate_builder
import cr8tor.core.resourceops as project_resources
from pathlib import Path
from datetime import datetime
from typing import Optional


def close_create_action_command(
    command_type: schemas.Cr8torCommandType,
    start_time: datetime,
    project_id: str,
    agent: str,
    project_resource_path: Path,
    resources_dir: Path,
    exit_msg: str,
    exit_code: int,
    instrument: str,
    result: Optional[list] = [],
    dryrun: Optional[bool] = False,
    config_file: Optional[Path] = "./config.toml",
):
    """
    CreateAction
    """

    if exit_code == schemas.Cr8torReturnCode.SUCCESS:
        status_type = schemas.ActionStatusType.COMPLETED
        err = None
    else:
        status_type = schemas.ActionStatusType.FAILED
        err = exit_msg

    action_props = schemas.CreateActionProps(
        id=f"{command_type}-{project_id}",
        name=f"{command_type} Data Project Action",
        start_time=start_time,
        end_time=datetime.now(),
        action_status=status_type,
        agent=agent,
        error=err,
        instrument=instrument,
        result=result,
    )

    project_resources.delete_resource_entity(
        project_resource_path, "actions", "id", f"{command_type}-{project_id}"
    )
    project_resources.update_resource_entity(
        project_resource_path, "actions", action_props.model_dump()
    )

    ro_crate_builder.build(resources_dir, config_file, dryrun)
    exit_command(command_type, exit_code, exit_msg)


def close_assess_action_command(
    command_type: schemas.Cr8torCommandType,
    start_time: datetime,
    project_id: str,
    agent: str,
    project_resource_path: Path,
    resources_dir: Path,
    exit_msg: str,
    exit_code: int,
    instrument: str,
    additional_type: Optional[str] = None,
    result: Optional[list] = [],
):
    """
    AssessAction
    """

    if exit_code == schemas.Cr8torReturnCode.SUCCESS:
        status_type = schemas.ActionStatusType.COMPLETED
        err = None
    else:
        status_type = schemas.ActionStatusType.FAILED
        err = exit_msg

    action_props = schemas.AssessActionProps(
        id=f"{command_type}-{project_id}",
        name=f"{command_type} Data Project Action",
        start_time=start_time,
        end_time=datetime.now(),
        action_status=status_type,
        agent=agent,
        error=err,
        instrument=instrument,
        additional_type=additional_type,
        result=result,
    )

    #
    # This assumes validate can be run multiple times on a project
    # Ensures previous run entities for this action are cleared in "actions" before
    # actions is updated with the new action entity
    #

    project_resources.delete_resource_entity(
        project_resource_path, "actions", "id", f"{command_type}-{project_id}"
    )
    project_resources.update_resource_entity(
        project_resource_path, "actions", action_props.model_dump()
    )

    ro_crate_builder.build(resources_dir)
    exit_command(command_type, exit_code, exit_msg)


def exit_command(
    command_type: schemas.Cr8torCommandType, exit_code: int, exit_msg: str
):
    """
    Exit the command with the appropriate success or error code and message
    """
    if exit_code == schemas.Cr8torReturnCode.SUCCESS:
        typer.echo(f"{exit_msg}")
    else:
        typer.echo(
            f"'{command_type}' command failed with {exit_code.name} (code {exit_code}): {exit_msg}",
            err=True,
        )
        raise typer.Exit(code=exit_code)
