"""Module with functions to initiate a CR8 project"""

from datetime import datetime
from typing import Annotated
from pathlib import Path

import git
import typer
import json
import os
import re
import time

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

    extra_context = {
        "__timestamp": datetime.now().isoformat(timespec="seconds"),
        "__cr8_cc_template": template_path,
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
        create_and_push_project(gh_client, project_dir, repo_name)

        # Check and create contributor teams
        check_and_create_teams(gh_client, repo_name)

        # Create repository environments for Signing Off experience
        create_github_environments(gh_client, repo_name)


def create_and_push_project(
    gh_client: gh_rest_api_client.GHApiClient,
    project_dir: str,
    repo_name: str,
):
    """

    Create a GitHub repository and push the generated project.

    Args:
        gh_client (GHApiClient): The GitHub API client.
        project_dir (str): The local directory of the generated project.
        repo_name (str): The repository name to be created.

    """

    # Step 1: Check if the repository already exists
    response = gh_client.get_repository(repo_name)

    if response:
        # Repository already exists, skip creation
        log.info(
            f"GitHub repository '{gh_client.git_org}/{repo_name}' already exists. Skipping creation..."
        )
        return

    # Step 2: Create a new repository under the organization
    response = gh_client.create_repository(repo_name)

    if response:
        log.info(
            f"GitHub repository '{gh_client.git_org}/{repo_name}' created successfully."
        )
    else:
        raise ValueError(f"Failed to create GitHub repository: {response}")

    # Step 3: Initialize git, add, commit and push the local project
    try:
        repo = git.Repo.init(project_dir)
        repo.git.checkout("-b", "main")  # Ensure 'main' branch exists
        repo.git.add(A=True)
        repo.index.commit("Initial commit")

        auth_repo_url = f"https://{os.getenv('GH_TOKEN')}@github.com/{gh_client.git_org}/{repo_name}.git"
        repo.create_remote("origin", auth_repo_url)
        repo.git.push("--set-upstream", "origin", "main")
        log.info(
            f"Project pushed to GitHub repository '{gh_client.git_org}/{repo_name}'."
        )
    except Exception as e:
        raise ValueError(f"An error occurred while pushing to GitHub: {e}")

    # Step 4: Apply the rule set for the repository
    project_repo_ruleset_path = Path(project_dir).joinpath(
        ".github", "branch_rules", "protect_main.json"
    )
    with project_repo_ruleset_path.open("r") as f:
        project_repo_ruleset = json.load(f)

    response = gh_client.create_repo_ruleset(repo_name, project_repo_ruleset)

    if response:
        log.info(f"Rule set applied for {repo_name}")
    else:
        raise ValueError(f"Failed to apply Repo rulesets: {response}")


def check_and_create_teams(
    gh_client: gh_rest_api_client.GHApiClient,
    repo_name: str,
) -> None:
    """

    Ensure GitHub teams exist and assign repository permissions.

    Args:
        gh_client (GHApiClient): The GitHub API client.
        repo_name (str): The repository name.

    """

    contributor_team = f"{repo_name}-contributor"
    # there is currently a single approver team for all projects
    approver_team = "cr8-ALL-projects-approver"
    devops_admin_team = "devops_admin"

    team_response = gh_client.get_team(contributor_team)
    team_slug = team_response["slug"] if team_response else None

    if not team_slug:
        team_slug = gh_client.create_team(
            contributor_team, f"Team for contributor members for project {repo_name}"
        )["slug"]
        log.info(f"Created team {contributor_team}")

        # wait 5 seconds for the team to be created in GitHub...
        time.sleep(5)

    else:
        log.info(f"Team {contributor_team} already exists. Skipping creation...")

    gh_client.add_or_update_team_repository_permission(
        repo_name, devops_admin_team, permission="push"
    )
    log.info(
        f"Added {repo_name} repository with 'push/write' permission to GitHub Team {devops_admin_team}"
    )

    gh_client.add_or_update_team_repository_permission(
        repo_name, team_slug, permission="push"
    )
    log.info(
        f"Added {repo_name} repository with 'push/write' permission to GitHub Team {contributor_team}"
    )

    gh_client.add_or_update_team_repository_permission(
        repo_name, approver_team, permission="pull"
    )
    log.info(
        f"Added {repo_name} repository with 'pull/read' permission to GitHub Team {approver_team}"
    )


def create_github_environments(
    gh_client: gh_rest_api_client.GHApiClient, repo_name: str
) -> None:
    """
    Create GitHub repository environments.

    Args:
        gh_client (GHApiClient): The GitHub API client.
        repo_name (str): The repository name.
    """

    # Create signoff environment
    gh_client.create_or_update_repo_env(
        repo_name, "signoff", ["cr8-ALL-projects-approver"]
    )
    log.info(f"Created Signing Off environment for {repo_name}")

    # Create the Production environment
    gh_client.create_or_update_repo_env(
        repo_name, "disclosure", ["cr8-ALL-projects-approver"]
    )
    log.info(f"Created Disclosure environment for {repo_name}")
