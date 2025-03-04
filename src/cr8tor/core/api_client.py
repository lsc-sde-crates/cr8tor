import httpx
import os
from pydantic import BaseModel
from typing import Optional, Union, Literal, Any, Dict
from dotenv import load_dotenv, find_dotenv
import json
from cr8tor.core.schema import (
    DataContractProjectRequest,
    DataContractValidateRequest,
    DataContractStageTransferRequest,
)


class HTTPResponse(BaseModel, frozen=True):
    status: Literal["success", "error"]
    action_type: Literal["assessAction", "createAction"]
    action: Literal["validate", "approve"]
    description: Optional[str] = None
    message: str
    payload: Dict[str, Any]


class SuccessResponse(BaseModel):
    # status: Literal["success"]
    # payload: dict
    class Config:
        extra = "allow"


class ErrorResponse(BaseModel):
    status: Literal["error"]
    # error_code: str
    payload: Dict[str, Any]


class APIClient:
    def __init__(self, base_url: str, token: str, port: Optional[int] = None):
        self.base_url = f"{base_url}:{port}" if port else base_url
        self.token = token
        self.client = httpx.AsyncClient(timeout=60 * 60)

    def get_headers(self) -> dict:
        return {
            # "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "x-api-key": f"{self.token}",
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
            raise RuntimeError(f"GET Request {url} failed: {exc}") from exc

    async def post(
        self, endpoint: str, data: dict = None
    ) -> Union[SuccessResponse, ErrorResponse]:
        url = f"{self.base_url}/{endpoint}"
        try:
            print(data)
            response = await self.client.post(
                url, json=data, headers=self.get_headers()
            )
            return self.handle_response(response)
        except httpx.RequestError as exc:
            raise RuntimeError(f"POST request {url} failed: {exc}") from exc

    async def put(
        self, endpoint: str, data: dict = None
    ) -> Union[SuccessResponse, ErrorResponse]:
        url = f"{self.base_url}/{endpoint}"
        try:
            response = await self.client.put(url, json=data, headers=self.get_headers())
            return self.handle_response(response)
        except httpx.RequestError as exc:
            raise RuntimeError(f"PUT request {url} failed: {exc}") from exc

    async def delete(self, endpoint: str) -> Union[SuccessResponse, ErrorResponse]:
        url = f"{self.base_url}/{endpoint}"
        try:
            response = await self.client.delete(url, headers=self.get_headers())
            return self.handle_response(response)
        except httpx.RequestError as exc:
            raise RuntimeError(f"DELETE Request {url} failed: {exc}") from exc

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
    load_dotenv(find_dotenv())
    # token = os.getenv("GITHUB_TOKEN")
    # if not token:
    #    raise ValueError("GITHUB_TOKEN environment variable is not set")
    if service == "MetaDataService":
        base_url = os.getenv("METADATA_HOST")
        port = os.getenv("METADATA_PORT")
        if not base_url and not port:
            raise ValueError("METADATA environment variables not set")
        token = os.getenv("METADATA_API_TOKEN")
    elif service == "ApprovalService":
        base_url = os.getenv("APPROVALS_HOST")
        port = os.getenv("APPROVALS_PORT")
        if not base_url or not port:
            raise ValueError("APPROVALS environments variable not set")
        token = os.getenv("APPROVALS_API_TOKEN")
    else:
        raise ValueError(f"Unknown service: {service}")

    return APIClient(base_url, token, port)


async def validate_access(access_info: DataContractValidateRequest) -> HTTPResponse:
    test = os.getenv("USE_TEST_DATA", "false").lower() == "true"
    if test:
        json_str = """{
    "status": "success",
    "payload": {
        "name": "pr001",
        "description": "This is test metadata for a test project comprising a few tables",
        "schema_name": "z__cr8tor_poc",
        "tables": [
            {
                "name": "concept",
                "description": "",
                "columns": [
                    {
                        "name": "concept_class_id",
                        "description": "",
                        "datatype": "STRING"
                    },
                    {
                        "name": "concept_code",
                        "description": "",
                        "datatype": "STRING"
                    },
                    {
                        "name": "concept_id",
                        "description": "",
                        "datatype": "LONG"
                    },
                    {
                        "name": "concept_name",
                        "description": "",
                        "datatype": "STRING"
                    },
                    {
                        "name": "domain_id",
                        "description": "",
                        "datatype": "STRING"
                    },
                    {
                        "name": "inserted_date_time",
                        "description": "",
                        "datatype": "TIMESTAMP"
                    },
                    {
                        "name": "inserted_process_instance_id",
                        "description": "",
                        "datatype": "STRING"
                    },
                    {
                        "name": "inserted_process_queue_id",
                        "description": "",
                        "datatype": "STRING"
                    },
                    {
                        "name": "invalid_reason",
                        "description": "",
                        "datatype": "STRING"
                    },
                    {
                        "name": "source_system",
                        "description": "",
                        "datatype": "STRING"
                    },
                    {
                        "name": "standard_concept",
                        "description": "",
                        "datatype": "STRING"
                    },
                    {
                        "name": "updated_date_time",
                        "description": "",
                        "datatype": "TIMESTAMP"
                    },
                    {
                        "name": "updated_process_instance_id",
                        "description": "",
                        "datatype": "STRING"
                    },
                    {
                        "name": "updated_process_queue_id",
                        "description": "",
                        "datatype": "STRING"
                    },
                    {
                        "name": "valid_end_date",
                        "description": "",
                        "datatype": "DATE"
                    },
                    {
                        "name": "valid_start_date",
                        "description": "",
                        "datatype": "DATE"
                    },
                    {
                        "name": "vocabulary_id",
                        "description": "",
                        "datatype": "STRING"
                    }
                ]
            }
        ]
    }
}"""
        return json.loads(json_str)["payload"]

    service = "ApprovalService"
    async with get_service_api(service) as approval_service_client:
        response = await approval_service_client.post(
            endpoint="project/validate", data=access_info.model_dump(mode="json")
        )
        if isinstance(response, SuccessResponse):
            print("Success:", response)
        else:
            print("Error:", response)
            raise Exception(response)
        return response.payload


async def stage_transfer(access_info: DataContractStageTransferRequest) -> HTTPResponse:
    test = os.getenv("USE_TEST_DATA", "false").lower() == "true"
    if test:
        json_str = """{
            "status": "success",
            "payload": {
                "data_retrieved": [
                    {
                        "file_path": "lsc/staging/data/outputs/database.duckdb"
                    }
                ]
            }
        }"""
        return json.loads(json_str)

    service = "ApprovalService"
    async with get_service_api(service) as approval_service_client:
        response = await approval_service_client.post(
            endpoint="project/package", data=access_info.model_dump(mode="json")
        )
        if isinstance(response, SuccessResponse):
            print("Success:", response)
        else:
            print("Error:", response)
        return response.payload


async def publish(access_info: DataContractProjectRequest) -> HTTPResponse:
    test = os.getenv("USE_TEST_DATA", "false").lower() == "true"
    if test:
        json_str = """{
            "status": "success",
            "payload": {
                "data_published": [
                    {
                        "file_path": "lsc/production/data/outputs/database.duckdb",
                        "hash_value": "f12190d5b8bd373103a6ecbd3e6f059d211c85fc3843888115c53f647c806afffdb2a55a6d98af4c78ecf5ee534d044a708240696a5852b484928ee10580f087",
                        "total_bytes": 1585152
                    }
                ]
            }
        }"""
        return json.loads(json_str)

    service = "ApprovalService"
    async with get_service_api(service) as approval_service_client:
        response = await approval_service_client.post(
            endpoint="project/publish", data=access_info.model_dump(mode="json")
        )
        if isinstance(response, SuccessResponse):
            print("Success:", response)
        else:
            print("Error:", response)
        return response.payload


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


# async def main():
#     pass


# if __name__ == "__main__":
#     asyncio.run(main())
