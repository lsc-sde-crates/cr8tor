from typing import Any, Dict
from pathlib import Path

import requests
import os
import git
import json
import time

from cr8tor.utils import log


class GHApiClient:
    def __init__(self, git_org: str):
        self.base_url = "https://api.github.com"
        self.git_org = git_org

    def get_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {os.getenv('GH_TOKEN')}",
            "Content-Type": "application/json",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def get(self, endpoint: str, params: dict = None):
        url = f"{self.base_url}/{endpoint}"
        try:
            response = requests.get(url, params=params, headers=self.get_headers())
            return response
        except requests.RequestException as exc:
            raise RuntimeError(f"GET Request {url} failed: {exc}") from exc

    def post(self, endpoint: str, json: dict = None):
        url = f"{self.base_url}/{endpoint}"
        try:
            response = requests.post(url, json=json, headers=self.get_headers())
            return response
        except requests.RequestException as exc:
            raise RuntimeError(f"POST Request {url} failed: {exc}") from exc

    def put(self, endpoint: str, json: dict = None):
        url = f"{self.base_url}/{endpoint}"
        try:
            response = requests.put(url, json=json, headers=self.get_headers())
            return response
        except requests.RequestException as exc:
            raise RuntimeError(f"PUT Request {url} failed: {exc}") from exc

    def get_team(self, team_slug):
        # https://docs.github.com/en/rest/teams/teams?apiVersion=2022-11-28#get-a-team-by-name
        endpoint = f"orgs/{self.git_org}/teams/{team_slug}"
        response = self.get(endpoint)

        # 404 means team not found. For all other errors, raise exception
        if response.status_code != 404:
            response.raise_for_status()

        return response.json() if response.ok else None

    def create_team(self, team_name, description):
        # https://docs.github.com/en/rest/teams/teams?apiVersion=2022-11-28#create-a-team
        endpoint = f"orgs/{self.git_org}/teams"

        payload = {
            "name": team_name,
            "description": description,
            "permission": "push",
            "notification_setting": "notifications_enabled",
            "privacy": "closed",
        }

        response = self.post(endpoint, json=payload)
        response.raise_for_status()
        return response.json() if response.ok else None

    def add_or_update_team_repository_permission(
        self, repo_name, team_slug, permission="push"
    ):
        # https://docs.github.com/en/rest/teams/teams?apiVersion=2022-11-28#add-or-update-team-repository-permissions
        endpoint = (
            f"orgs/{self.git_org}/teams/{team_slug}/repos/{self.git_org}/{repo_name}"
        )

        payload = {"permission": permission}

        response = self.put(endpoint, json=payload)
        response.raise_for_status()
        return

    def get_repository(self, repo_name):
        # https://docs.github.com/en/rest/repos/repos?apiVersion=2022-11-28#get-a-repository
        endpoint = f"repos/{self.git_org}/{repo_name}"
        response = self.get(endpoint)
        # 404 means team not found. For all other errors, raise exception
        if response.status_code != 404:
            response.raise_for_status()
        return response.json() if response.ok else None

    def create_repository(self, repo_name):
        # https://docs.github.com/en/rest/repos/repos?apiVersion=2022-11-28#create-an-organization-repository
        endpoint = f"orgs/{self.git_org}/repos"
        payload = {
            "name": repo_name,
            "description": f"Data Access Request repository for project {repo_name}",
            "private": True,  # You can adjust this to make it private/public if needed. By default, it's private.
        }
        response = self.post(endpoint, json=payload)
        return response.json() if response.status_code == 201 else None

    def create_repo_ruleset(self, repo_name, ruleset: Dict[str, Any]):
        # https://docs.github.com/en/rest/repos/rules?apiVersion=2022-11-28#create-a-repository-ruleset
        endpoint = f"repos/{self.git_org}/{repo_name}/rulesets"
        response = self.post(endpoint, json=ruleset)
        response.raise_for_status()
        return response.json() if response.ok else None

    def create_or_update_repo_env(
        self, repo_name, enviroment_name, reviewers_team_list
    ):
        # https://docs.github.com/en/rest/deployments/environments?apiVersion=2022-11-28#create-or-update-an-environment
        endpoint = f"repos/{self.git_org}/{repo_name}/environments/{enviroment_name}"

        # reviewers should be like like [{"type":"Team","id":1},{"type":"Team","id":2},{"type":"User","id":3}]
        reviewers = []
        for team_name in reviewers_team_list:
            reviewers.append({"type": "Team", "id": self.get_team(team_name)["id"]})

        payload = {
            "reviewers": reviewers,
        }

        response = self.put(endpoint, json=payload)
        response.raise_for_status()
        return response.json() if response.ok else None


def create_and_push_project(
    gh_client: GHApiClient,
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
    gh_client: GHApiClient,
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


def create_github_environments(gh_client: GHApiClient, repo_name: str) -> None:
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
