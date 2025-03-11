"""Module with functions to initiate a CR8 project"""

from datetime import datetime
from typing import Annotated
from pathlib import Path

import typer
import re

from cookiecutter.main import cookiecutter
from cookiecutter.exceptions import OutputDirExistsException
from cr8tor.utils import log
import cr8tor.core.resourceops as project_resources
import cr8tor.core.schema as schemas
import cr8tor.core.gh_rest_api_client as gh_rest_api_client

app = typer.Typer()


@app.command(name="init")
def init(
    template_path: Annotated[
        str,
        typer.Option(
            default="-t",
            help="GitHub URL or relative path to cr8-cookiecutter template",
            prompt=True,
        ),
    ],
    push_to_github: Annotated[
        bool,
        typer.Option(
            "--push/--no-push",
            help="Flag to indicate if the project should be pushed to GitHub",
        ),
    ] = False,
    git_org: Annotated[
        str,
        typer.Option(
            "-org",
            help="Target github organisation name",
            hide_input=True,
        ),
    ] = None,
    checkout: Annotated[
        str,
        typer.Option(
            "-chk",
            help="Branch, tag or commit to checkout from cookiecutter template",
        ),
    ] = None,
    project_name: Annotated[
        str,
        typer.Option(
            "-n",
            help="Name of the project to be created. This is optional and can be provided as an argument.",
        ),
    ] = None,
    environment: Annotated[
        str,
        typer.Option(
            "-e",
            help="Target environment. Default PROD. Must be one of the three options: DEV, TEST, PROD.",
            case_sensitive=False,
            show_choices=True,
        ),
    ] = "PROD",
):
    """

    Initialize a new CR8 project using a specified cookiecutter template.

    Args:
        template_path (str): The GitHub URL or relative path to the cr8-cookiecutter template.
                            This is prompted from the user if not provided.
        push_to_github (bool): Flag to indicate if the project should be pushed to GitHub.
        git_org (Optional[str]): The target GitHub organization name.
        checkout (Optional[str]): The branch, tag, or commit to checkout from the cookiecutter template.
        project_name (Optional[str]): The name of the project to be created. If provided, cookiecutter will skip the prompt for other values.

    The function generates a new project by applying the specified cookiecutter template.
    It also adds a timestamp to the context used by the template.

    If `push_to_github` is True, it will also create a GitHub repository under the specified organization
    and push the generated project to GitHub using the provided personal access token (os.getenv("GH_TOKEN"))

    Example usage:

        cr8tor init -t https://github.com/lsc-sde-crates/cr8-cookiecutter

        or

        cr8tor init -t path-to-local-cr8-cookiecutter-dir

        or

        cr8tor init -t path-to-local-cr8-cookiecutter-dir -n "my-project" -org "lsc-sde-crates" --push
    """
    valid_environments = ["DEV", "TEST", "PROD"]
    if environment.upper() not in valid_environments:
        raise typer.BadParameter(
            f"Invalid environment. Choose from {valid_environments}."
        )

    extra_context = {
        "__timestamp": datetime.now().isoformat(timespec="seconds"),
        "__cr8_cc_template": template_path,
        "environment": environment.upper(),
    }

    # Generate the project with cookiecutter
    if project_name is not None:
        extra_context.update({"project_name": project_name})
        extra_context.update({"github_organization": git_org})
        try:
            project_dir = cookiecutter(
                template_path,
                checkout=checkout,
                extra_context=extra_context,
                no_input=True,
            )
        except OutputDirExistsException as e:
            log.info("Project directory already exists. Skipping creation...")
            # Extract folder name from exception message
            folder_name = re.search(r'"(.*?)"', str(e)).group(1)
            project_dir = Path.cwd() / folder_name
    else:
        try:
            project_dir = cookiecutter(
                template_path, checkout=checkout, extra_context=extra_context
            )
        except OutputDirExistsException as e:
            log.info("Project directory already exists. Skipping creation...")
            # Extract folder name from exception message
            folder_name = re.search(r'"(.*?)"', str(e)).group(1)
            project_dir = Path.cwd() / folder_name

    resources_dir = Path(project_dir).joinpath("resources")
    project_resource_path = resources_dir.joinpath("governance", "project.toml")
    project_dict = project_resources.read_resource_entity(
        project_resource_path, "project"
    )
    project_info = schemas.ProjectProps(**project_dict)

    if push_to_github and git_org:
        repo_name = project_info.reference

        gh_client = gh_rest_api_client.GHApiClient(git_org)

        # Create the repository and push the project to GitHub
        gh_rest_api_client.create_and_push_project(gh_client, project_dir, repo_name)

        # Check and create contributor teams
        gh_rest_api_client.check_and_create_teams(gh_client, repo_name)

        # Create repository environments for Signing Off experience
        gh_rest_api_client.create_github_environments(gh_client, repo_name)
