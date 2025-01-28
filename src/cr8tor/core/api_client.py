import httpx
import asyncio
import os
from pydantic import BaseModel
from typing import Optional, Union, Literal, Any, Dict
from dotenv import load_dotenv, find_dotenv


class HTTPResponse(BaseModel, frozen=True):
    status: Literal["success", "error"]
    action: Literal["validate", "approve"]
    action_type: Literal["assessAction", "createAction"]
    description: Optional[str] = None
    message: str
    action_metadata: Dict[str, Any]


class SuccessResponse(HTTPResponse):
    status: Literal["success"]


class ErrorResponse(HTTPResponse):
    status: Literal["error"]
    error_code: str


class APIClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.token = token
        self.client = httpx.AsyncClient()

    def get_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    async def get(
        self, endpoint: str, params: dict = None
    ) -> Union[SuccessResponse, ErrorResponse]:
        url = f"{self.base_url}/{endpoint}"
        try:
            response = await self.client.get(
                url, params=params, headers=self.get_headers()
            )
            return self.handle_response(response)
        except httpx.RequestError as exc:
            raise RuntimeError(f"Request failed: {exc}") from exc

    async def post(
        self, endpoint: str, data: dict = None
    ) -> Union[SuccessResponse, ErrorResponse]:
        url = f"{self.base_url}/{endpoint}"
        try:
            response = await self.client.post(
                url, json=data, headers=self.get_headers()
            )
            return self.handle_response(response)
        except httpx.RequestError as exc:
            raise RuntimeError(f"Request failed: {exc}") from exc

    async def put(
        self, endpoint: str, data: dict = None
    ) -> Union[SuccessResponse, ErrorResponse]:
        url = f"{self.base_url}/{endpoint}"
        try:
            response = await self.client.put(url, json=data, headers=self.get_headers())
            return self.handle_response(response)
        except httpx.RequestError as exc:
            raise RuntimeError(f"Request failed: {exc}") from exc

    async def delete(self, endpoint: str) -> Union[SuccessResponse, ErrorResponse]:
        url = f"{self.base_url}/{endpoint}"
        try:
            response = await self.client.delete(url, headers=self.get_headers())
            return self.handle_response(response)
        except httpx.RequestError as exc:
            raise RuntimeError(f"Request failed: {exc}") from exc

    def handle_response(
        self, response: httpx.Response
    ) -> Union[SuccessResponse, ErrorResponse]:
        if response.status_code == 200:
            return SuccessResponse(**response.json())
        else:
            return ErrorResponse(**response.json())

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.client.aclose()


def get_service_api(service: str) -> APIClient:
    # token = os.getenv("GITHUB_TOKEN")
    # if not token:
    #    raise ValueError("GITHUB_TOKEN environment variable is not set")
    if service == "MetaDataService":
        base_url = os.getenv("METADATA_BASE_URL")
        if not base_url:
            raise ValueError("METADATA_BASE_URL environment variable not set")
        token = os.getenv("METADATA_API_TOKEN", "123")
    elif service == "ApprovalService":
        base_url = os.getenv("APPROVAL_BASE_URL")
        if not base_url:
            raise ValueError("APPROVAL_BASE_URL environment variable not set")
        token = os.getenv(
            "APPROVAL_API_TOKEN", "123"
        )  # TODO: change to real token from github secrets
    else:
        raise ValueError(f"Unknown service: {service}")

    return APIClient(base_url, token)


async def validate_access(project_url: str) -> HTTPResponse:
    service = "MetaDataService"
    async with get_service_api(service) as metadata_service_client:
        response = await metadata_service_client.post(
            "validate", data={"project_url": project_url}
        )
        if isinstance(response, SuccessResponse):
            print("Success:", response)
        else:
            print("Error:", response)
        return response


async def approve(project_url: str) -> HTTPResponse:
    service = "ApprovalService"
    async with get_service_api(service) as approval_service_client:
        response = await approval_service_client.post(
            "approve", data={"project_url": project_url}
        )
        if isinstance(response, SuccessResponse):
            print("Success:", response)
        else:
            print("Error:", response)
        return response


async def main():
    # testing
    await validate_access("http://example.com/ro-crate-123")


if __name__ == "__main__":
    load_dotenv(find_dotenv())
    asyncio.run(main())
