import os
import typer
import cr8tor.core.schema as s
import cr8tor.cli.build as ro_crate_builder
import cr8tor.core.resourceops as project_resources
import cr8tor.core.crate_graph as proj_graph

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
    Log sign-off metadata in RO-Crate and verify project sign-off in approvals management platform (i.e. github)

    Args:
        review_url (str): URL to the project sign off event.
        agent (str): Label of the agent performing cr8tor sign-off execution.
        bag_dir (Path): The Bagit directory containing the RO-Crate data directory.
                        Defaults to "./bagit".
        resources_dir (Path): The directory containing resources to include in the RO-Crate.
                              Defaults to "./resources".

    This command updates the project approvals metadata

    Example usage:

        cr8tor sign-off -agreement <url_to_approved_policy> -signing-entity <entity_name>

    """

    if agent is None:
        agent = os.getenv("APP_NAME")

    start_time = datetime.now()
    project_resource_path = resources_dir.joinpath("governance", "project.toml")
    project_dict = project_resources.read_resource_entity(
        project_resource_path, "project"
    )
    project_info = s.ProjectProps(**project_dict)

    current_rocrate_graph = proj_graph.ROCrateGraph(bagit_dir)
    if not current_rocrate_graph.is_validated():
        typer.echo(
            "The project must be validated before sign off / approval can be completed.",
            err=True,
        )
        raise typer.Exit(code=1)

    is_valid = True
    err = None

    #
    # Should we verify that the approved PR URI exists?
    #

    statusType = s.ActionStatusType.COMPLETED if is_valid else s.ActionStatusType.FAILED

    assess_action_props = s.AssessActionProps(
        id=f"sign-off-{project_info.id}",
        name="IG Sign-Off Project Action",
        start_time=start_time,
        end_time=datetime.now(),
        action_status=statusType,
        agent=agent,
        error=err,
        instrument=f"{signing_entity}",
        additional_type="Sign off",
        result=[{"@id": agreement_url}],
    )

    project_resources.delete_resource_entity(
        project_resource_path, "actions", "id", f"sign-off-{project_info.id}"
    )
    project_resources.update_resource_entity(
        project_resource_path, "actions", assess_action_props.model_dump()
    )

    ro_crate_builder.build(resources_dir)
