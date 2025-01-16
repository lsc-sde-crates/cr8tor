from enum import StrEnum
from typing import List
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

#
# Application managed data classes for entities not defined as classes in rocrate module 
#

class Organization(BaseModel):
    name: str

class SoftwareApplication(BaseModel):
    name: str
    provider: Organization

class Agent(BaseModel):
    name: str

class Instrument(BaseModel):
    name: str

class ActionStatusType(StrEnum):
    active_action_status: str = "ActiveActionStatus"
    completed_action_status: str = "CompletedActionStatus"
    failed_action_status: str = "FailedActionStatus"
    potential_action_status: str = "PotentialActionStatus"

class Action(BaseModel):
    name: str
    end_time: datetime
    start_time: datetime
    action_status: ActionStatusType
    agent: Agent
    error: Optional[str] = None
    instrument: Optional[Instrument] = None
    
class CreateAction(Action):
    result: List[str]

class AssessAction(Action):
    additional_type: str    

#
# Claases to model user-defined properties specified in resources TOML
#

#
# Data access
#

class DataContract(BaseModel):
    source: str
    url: str
    service_principal_key: str # key vault key holding auth info
    secret_provider: str # i.e. Key Vault


class CrateMeta(StrEnum):
    License: str = '<a href="https://opensource.org/license/mit">MIT License</a>'
    Publisher: str = '<a href="https://github.com/lsc-sde-crates">LSC SDE</a>'


class Project(BaseModel):
    """
    The project that the request is sent on behalf of, typically related to permission to use a TRE,
    MUST be indicated from the root dataset using sourceOrganization to a Project. The responsible
    project SHOULD be referenced from the requesting agent’s memberOf.

    https://trefx.uk/5s-crate/0.5-DRAFT/#responsible-project

    https://schema.org/Project
    """

    name: str
    description: str
    identifier: str


class CodeRepository(BaseModel):
    """
    External Github repository used to manage this LSCSDE project
    """
    name: str
    description: str
    url: str

class Affiliation(BaseModel):
    name: str
    url: str

class Requester(BaseModel):
    """
    The individual person who is requesting the run MUST be indicated as an `agent` from the
    `CreateAction`, which SHOULD have an `affiliation` to the organisation they are representing
    for access control purposes

    https://trefx.uk/5s-crate/0.5-DRAFT/#requesting-agent
    """

    name: str
    affiliation: Affiliation


class ColumnMetadata(BaseModel):
    name: str
    description: str
    datatype: str


class TableMetadata(BaseModel):
    name: str
    description: str
    columns: List[ColumnMetadata]


class DatasetMetadata(BaseModel):
    name: str
    description: str
    catalog: str
    table_schema: str
    tables: List[TableMetadata]

class BagitInfo(BaseModel):
    source_organization: str = Field(alias="Source-Organization")
    organization_address: str = Field(alias="Organization-Address")
    contact_name: str = Field(alias="Contact-Name")
    contact_email: str = Field(alias="Contact-Email")
