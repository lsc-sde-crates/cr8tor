"""Pydantic models to validate properties of schema.org entities and other resources that will go within the RO-Crate"""

from enum import StrEnum, IntEnum
from typing import List
from pydantic import BaseModel, Field, HttpUrl, field_validator
from datetime import datetime
from typing import Optional, Literal, Union


###############################################################################
# Models to validate properties of Schema.org entities
###############################################################################

# Pydantic model names should follow the convention of ThingProps eg. PersonProps
# Where one of the properties is a reference to another schema.org entity,
# this should be of type Any or str and optional, rather than a reference to the ThingProps of that entity
# For instance, Person may have an affiliation property. This should not be of type AffiliationProps.


class BaseRoCrateEntityProperties(BaseModel):
    id: Optional[str] = Field(
        default=None,
        alias="@id",
        description="Mandatory identifier of entity. This needs to be unique within the context of the ro-crate knowledge graph",
    )
    type: Optional[str] = Field(
        default=None, alias="@type", description="Mandatory type of entity"
    )
    description: Optional[str] = Field(default=None, description="Entity desc")

    class Config:
        populate_by_name = True
        json_encoders = {HttpUrl: str}


class ProjectProps(BaseRoCrateEntityProperties):
    """
    The project that the request is sent on behalf of, typically related to permission to use a TRE,
    MUST be indicated from the root dataset using sourceOrganization to a Project. The responsible
    project SHOULD be referenced from the requesting agent’s memberOf.

    https://trefx.uk/5s-crate/0.5-DRAFT/#responsible-project

    https://schema.org/Project
    """

    type: Literal["Project"] = Field(default="Project", alias="@type")
    name: str
    description: str
    reference: str


class OrganizationProps(BaseRoCrateEntityProperties):
    name: str = Field(description="Organisation name e.g. Lancaster University")
    url: HttpUrl = Field(description="Organisation URL")


class PersonProps(BaseRoCrateEntityProperties):
    name: str = Field(description="An individual's name")
    url: HttpUrl = Field(description="Organisation URL")


class SoftwareApplicationProps(BaseRoCrateEntityProperties):
    type: Literal["SoftwareApplication"] = Field(
        default="SoftwareApplication", alias="@type"
    )
    name: str = Field(description="Software application name")
    provider: Union[OrganizationProps, PersonProps] = Field(
        description="Software provider. Can be organization or Person"
    )


class SoftwareSourceCodeProps(BaseRoCrateEntityProperties):
    type: Literal["SoftwareSourceCode"] = Field(
        default="SoftwareSourceCode", alias="@type"
    )
    name: str = Field(description="repo name")
    codeRepository: Optional[HttpUrl] = Field(default=None, description="repo url")


class ActionStatusType(StrEnum):
    ACTIVE: str = "ActiveActionStatus"
    COMPLETED: str = "CompletedActionStatus"
    FAILED: str = "FailedActionStatus"
    POTENTIAL: str = "PotentialActionStatus"


class ResultItem(BaseModel):
    class Config:
        extra = "allow"


class ActionProps(BaseRoCrateEntityProperties, use_enum_values=True):
    type: Literal["Action"] = Field(default="Action", alias="@type")
    name: str = Field(description="Action name")
    start_time: datetime = Field(description="Start time of the action")
    end_time: datetime = Field(description="End time of the action")
    action_status: ActionStatusType = Field(
        description="Status of the action formmatted based on Provernance Crate Profile spec"
    )
    result: List[ResultItem] = Field(
        description="Id references to other data or context entities"
    )
    agent: str = Field(
        description="The thing triggering the action i.e. a person, organisation or software application (e.g. Github Action)"
    )
    error: Optional[str] = Field(
        default=None, description="Error output if action fails"
    )
    instrument: Optional[str] = Field(
        default=None,
        description="Instrument performing the execution of the action (e.g. cr8tor, specific TRE service)",
    )

    @field_validator("action_status", mode="before")
    @classmethod
    def convert_to_enum(cls, v):
        """Converts a string value to an ActionStatusType enum."""
        if isinstance(v, str):
            try:
                return ActionStatusType(v)
            except ValueError:
                raise ValueError(
                    f"Invalid action_status: '{v}'. Must be one of {list(ActionStatusType)}"
                )
        return v


class CreateActionProps(ActionProps):
    type: Literal["CreateAction"] = Field(default="CreateAction", alias="@type")


class AssessActionProps(ActionProps):
    type: Literal["AssessAction"] = Field(default="AssessAction", alias="@type")

    additional_type: Optional[str] = Field(
        default=None,
        description="Use to reference sub assessment actions (e.g. disclosure check)",
    )


class AffiliationProps(BaseRoCrateEntityProperties):
    name: str
    url: str


class AgentProps(BaseRoCrateEntityProperties):
    """
    Model represents an individual person who is an agent triggering an cr8tor action,
    which SHOULD have an `affiliation` to the organisation they are representing
    for access control purposes. Based on the requesting-agent model in the 5S-Crate spec.

    https://trefx.uk/5s-crate/0.5-DRAFT/#requesting-agent
    """

    name: str
    affiliation: OrganizationProps


###############################################################################
# Models to validate other entities that are unrelated to Schema.org entities
###############################################################################


class ProjectInit(BaseModel):
    project_name: str = Field(
        default="CR8TOR Demo Project",
        description="The title of the data access project",
    )
    identifier: str = Field(
        description="Internal/organisation project reference (not the UUID of the project)."
    )
    project_description: Optional[str] = Field(
        description="Detailed description of the project"
    )
    requester: Optional[str] = ""
    requester_affiliation: Optional[str] = ""
    requester_affiliation_url: Optional[str] = ""
    timestamp: Optional[str] = ""


class CrateMeta(StrEnum):
    License: str = '<a href="https://opensource.org/license/mit">MIT License</a>'
    Publisher: str = '<a href="https://github.com/lsc-sde-crates">LSC SDE</a>'


class ColumnMetadata(BaseModel):
    name: str
    datatype: Optional[str] = None
    description: Optional[str] = None


class TableMetadata(BaseModel):
    name: str
    columns: Optional[List[ColumnMetadata]] = None
    description: Optional[str] = None


class DatasetMetadata(BaseModel):
    name: str
    schema_name: str
    description: Optional[str] = Field(
        description="A dataset comprising one or more tables"
    )
    tables: Optional[List[TableMetadata]] = None
    staging_path: Optional[dict] = None
    publish_path: Optional[dict] = None


class AffiliationInfo(BaseModel):
    name: str = Field(description="Name of affiliation e.g. Lancaster University")
    url: str = Field(description="URL of affiliate organisation")


class Approver(BaseModel):
    name: str = Field(
        description="Person/team responsible for approving/signing off on the request"
    )
    affiliation: AffiliationInfo = Field(description="Affiliation of the approver")


class DiscloureReviewer(BaseModel):
    name: str = Field(description="Person/team responsible for disclosure checks")
    affiliation: AffiliationInfo = Field(description="Affiliation of the approver")


class BagitInfo(BaseModel):
    source_organization: str = Field(alias="Source-Organization")
    organization_address: str = Field(alias="Organization-Address")
    contact_name: str = Field(alias="Contact-Name")
    contact_email: str = Field(alias="Contact-Email")


#
# User-defined data 'access' information from resources/access toml
#


class DataSourceConnection(BaseModel):
    name: Optional[str] = None
    type: str = Field(description="Data source type")


class DatabricksSourceConnection(DataSourceConnection):
    host_url: str = Field(description="dbs workspace URL")
    port: int = Field(
        default=443, description="Port for the db cluster (defaults to 443)"
    )
    catalog: str = Field(description="Unity catalog name")
    http_path: str = Field(description="Schema name in UC")


class SourceAccessCredential(BaseModel):
    provider: str | None = Field(
        default=None,
        description="Service providing the secrets e.g. KeyVault",
    )
    spn_clientid: str = Field(
        description="Key name in secrets provider to access spn clientid ",
    )
    spn_secret: str = Field(
        description="Key name in secrets provider to access spn secret",
    )


# class DataPublishContract(BaseModel):
#     """Model required for all publish endpoints."""

#     project_name: str = (
#         Field(description="Project name (without whitespaces)", pattern=r"^\S+$"),
#     )
#     project_start_time: str = (
#         Field(
#             description="Start time of the LSC project action. Format: YYYYMMDD_HHMMSS",
#             pattern=r"^\d{8}_\d{6}$",
#         ),
#     )
#     destination_type: str = Field(
#         description="Target SDE storage account where data should be loaded",
#         enum=["LSC", "NW"],
#     )
#     destination_format: Optional[str] = Field(
#         description="Target format for the data to be loaded",
#         default=None,
#     )


# class ValidateDataContractRequest(DataPublishContract):
#     source: Union[DataSourceConnection, DatabricksSourceConnection] = Field(
#         description="db connection details definition"
#     )
#     credentials: SourceAccessCredential = Field(
#         description="Auth provider and secrets key"
#     )
#     dataset: DatasetMetadata = Field(
#         description="Metadata for the requested tables",
#     )


#
# Service Request Models
#
class DataContractProjectRequest(BaseModel):
    project_name: str = (
        Field(description="Project name (without whitespaces)", pattern=r"^\S+$"),
    )
    project_start_time: str = (
        Field(
            description="Start time of the LSC project action. Format: YYYYMMDD_HHMMSS",
            pattern=r"^\d{8}_\d{6}$",
        ),
    )
    destination_type: str = Field(
        description="Target SDE storage account where data should be loaded",
        enum=["LSC", "NW"],
    )


class DataContractAccessRequest(DataContractProjectRequest):
    destination_format: str = Field(
        description="Target format for the data to be loaded",
        enum=["CSV", "DUCKDB"],
    )
    source: Union[DataSourceConnection, DatabricksSourceConnection] = Field(
        description="db connection details definition"
    )
    credentials: SourceAccessCredential = Field(
        description="Auth provider and secrets key"
    )


class DataContractValidateRequest(DataContractAccessRequest):
    dataset: DatasetMetadata = Field(
        description="Metadata for the requested tables",
    )


#
# TODO: Ask Piotr to make this 'dataset' not metadata like validate req
#
class DataContractStageTransferRequest(DataContractAccessRequest):
    metadata: DatasetMetadata = Field(
        description="Metadata for the requested tables",
    )


#
# Payload Response models
#


class StageTransferLocation(BaseModel):
    file_path: str


class StageTransferPayload(BaseModel):
    data_retrieved: List[StageTransferLocation]


class PublishLocation(BaseModel):
    file_path: str
    hash_value: str
    total_bytes: int


class PublishPayload(BaseModel):
    data_published: List[PublishLocation]


class HTTPPayloadResponse(BaseModel):
    status: str
    payload: Union[StageTransferPayload, PublishPayload]


class Cr8torReturnCode(IntEnum):
    SUCCESS = 0
    ACTION_WORKFLOW_ERROR = 1
    VALIDATION_ERROR = 2
    ACTION_EXECUTION_ERROR = 3
    UNKNOWN_ERROR = 3


class Cr8torCommandType(StrEnum):
    INITIATE: str = "Initiate"
    CREATE: str = "Create"
    VALIDATE: str = "Validate"
    SIGN_OFF: str = "Sign-Off"
    STAGE_TRANSFER: str = "Stage-Transfer"
    DISCLOSURE_CHECK: str = "Disclosure-Check"
    PUBLISH: str = "Publish"


class RoCrateActionType(StrEnum):
    CREATE: str = "CreateAction"
    ASSESS: str = "AssessAction"
