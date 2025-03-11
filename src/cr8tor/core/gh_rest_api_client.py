from typing import Any, Dict

import requests
import os


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
