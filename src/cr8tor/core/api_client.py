import httpx
import asyncio
import os
from pydantic import BaseModel
from typing import Optional, Union, Literal, Any, Dict


class HTTPResponse(BaseModel):
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
    if service == "ApprovalMicroSrv":
        base_url = "https://6c556f5b-f83e-42d0-94ca-5ade56f98b05.mock.pstmn.io"
        token = os.getenv("API_TOKEN", "123")  # Use environment variable or fallback
    elif service == "MetaDataMicroSrv":
        base_url = "https://metadata.service.url"  # Replace with actual URL
        token = os.getenv("METADATA_API_TOKEN", "abc")
    else:
        raise ValueError(f"Unknown service: {service}")

    return APIClient(base_url, token)


async def approve(project_url: str) -> HTTPResponse:
    service = "ApprovalMicroSrv"
    async with get_service_api(service) as approval_service_client:
        response = await approval_service_client.post(
            "approve", data={"project_url": project_url}
        )
        if isinstance(response, SuccessResponse):
            print("Success:", response)
        else:
            print("Error:", response)
        return response


async def validate(project_url: str) -> HTTPResponse:
    # service = "ApprovalMicroSrv"
    pass


async def main():
    # testing
    await approve("http://example.com/ro-crate-123")


if __name__ == "__main__":
    asyncio.run(main())
