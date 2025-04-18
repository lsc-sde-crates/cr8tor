import os
import typer
import cr8tor.core.schema as s
import cr8tor.core.resourceops as project_resources
import cr8tor.core.crate_graph as proj_graph
import cr8tor.cli.utils as cli_utils

from pathlib import Path
from typing import Annotated
from datetime import datetime

app = typer.Typer()


@app.command(name="sign-off")
def sign_off(
    agreement_url: Annotated[
        str,
        typer.Option(
            default="-agreement",
            help="URL to the project sign off event (i.e. PR event in project github history)",
        ),
    ],
    signing_entity: Annotated[
        str,
        typer.Option(
            default="-signing-entity",
            help="Entity that agreed to sign off the project request.",
        ),
    ],
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
    Logs sign-off metadata in the RO-Crate and verifies project sign-off in the approvals management platform (e.g., GitHub).

    Args:
        agreement_url (str): URL to the project sign-off event (e.g., PR event in the project's GitHub history).
        signing_entity (str): The entity that agreed to sign off the project request.
        agent (str): The agent label triggering the validation. Defaults to None.
        bagit_dir (Path): Path to the Bagit directory containing the RO-Crate data directory. Defaults to "./bagit".
        resources_dir (Path): Path to the directory containing resources to include in the RO-Crate. Defaults to "./resources".

    This command performs the following actions:
    - Updates the project approvals metadata in the RO-Crate.
    - Verifies the project sign-off in the approvals management platform.

    Example usage:
        cr8tor sign-off -agreement <url_to_approved_policy> -signing-entity <entity_name> -a <agent_label> -b <bagit_dir> -i <resources_dir>
    """

    if agent is None:
        agent = os.getenv("APP_NAME")

    start_time = datetime.now()
    project_resource_path = resources_dir.joinpath("governance", "project.toml")
    project_dict = project_resources.read_resource_entity(
        project_resource_path, "project"
    )
    project_info = s.ProjectProps(**project_dict)

    if not bagit_dir.exists():
        cli_utils.exit_command(
            s.Cr8torCommandType.SIGN_OFF,
            s.Cr8torReturnCode.ACTION_EXECUTION_ERROR,
            f"Missing bagit directory at: {bagit_dir}",
        )

    current_rocrate_graph = proj_graph.ROCrateGraph(bagit_dir)

    if not current_rocrate_graph.is_project_action_complete(
        command_type=s.Cr8torCommandType.VALIDATE,
        action_type=s.RoCrateActionType.ASSESS,
        project_id=project_info.id,
    ):
        cli_utils.close_assess_action_command(
            command_type=s.Cr8torCommandType.SIGN_OFF,
            start_time=start_time,
            project_id=project_info.id,
            agent=agent,
            project_resource_path=project_resource_path,
            resources_dir=resources_dir,
            exit_msg="The project must be validated before sign off / approval",
            exit_code=s.Cr8torReturnCode.ACTION_WORKFLOW_ERROR,
            instrument=f"{signing_entity}",
            additional_type="Sign off",
        )
    #
    # Should we verify that the approved PR URI exists here?
    #

    cli_utils.close_assess_action_command(
        command_type=s.Cr8torCommandType.SIGN_OFF,
        start_time=start_time,
        project_id=project_info.id,
        agent=agent,
        project_resource_path=project_resource_path,
        resources_dir=resources_dir,
        exit_msg="Sign off complete",
        exit_code=s.Cr8torReturnCode.SUCCESS,
        instrument=f"{signing_entity}",
        additional_type="Sign off",
        result=[{"@id": agreement_url}],
    )
