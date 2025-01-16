from enum import StrEnum
from typing import List
from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime
from typing import Optional, Literal

#
# Classes to represent resources/toml defined information
#

#
# User-defined data 'access' information from resources/access toml
#
class DataSourceConnection(BaseModel):
    name: Optional[str] = None

class DatabricksSourceConnection(DataSourceConnection):
    host_url: HttpUrl = Field(description="dbs workspace URL")
    port: int = Field(default=443, description="Port for the db cluster (defaults to 443)")
    catalog: str = Field(description="Unity catalog name")
    schema: str = Field(description="Schema name in UC")
    table: str = Field(description="Target table name")

class SourceAccessCredential(BaseModel):
    provider: str = Field(description="Service providing the secrets e.g. KeyVault")
    secret_name: str = Field(description="Key name in secrets provider to access token")   

class DataAccessContract(BaseModel):
    connection: DataSourceConnection = Field(description="db connection details definition")
    credentials: SourceAccessCredential = Field(description="Auth provider and secrets key")

#
# User-defined governance information from resources/governance toml
#

class Project(BaseModel):

    name: str = Field(description="The title of the data access project")
    description: str = Field(description="Detailed description of the project")
    identifier: str = Field(description="Internal/organisation project reference (not the UUID of the project).")

class CodeRepository(BaseModel):
 
    name: str = Field(description="Name given to project github repository")
    description: str = Field(description="MIKE TO REMOVE: Not needed to be defined by user")
    url: str = Field(description="Project github repository URL")

class Affiliation(BaseModel):

    name: str = Field(description="Name of affiliation e.g. Lancaster University")
    url: str = Field(description="URL of affiliate organisation")

class Requester(BaseModel):

    name: str = Field(description="Name of requesting agent i.e. the researcher that raised the data request")
    affiliation: Affiliation = Field(description="Affiliation of the requester")

class Approver(BaseModel):

    name: str = Field(description="Person/team responsible for approving/signing off on the request")
    affiliation: Affiliation = Field(description="Affiliation of the approver")

class DiscloureReviewer(BaseModel):
    
    name: str = Field(description="Person/team responsible for disclosure checks")
    affiliation: Affiliation = Field(description="Affiliation of the approver")

#
# Metadata classes. TODO: revise these based on returned outputs from unity catalog
#

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

#
# Application managed data classes for entities not defined as classes in ro-crate module 
# TODO: These should really be extensions within the ro-crate py module, discuss whether event/action info should be
# stored in the resources data or just in ro-crate metadata.json
# Think we should define these as models for the properties of ro-crate entities  

class Organization(BaseModel):
    name: str

class SoftwareApplication(BaseModel):
    name: str
    provider: Organization

class Agent(BaseModel):
    name: str

class Instrument(BaseModel):
    name: str
    # tool: str

class ActionStatusType(StrEnum):
    active_action_status: str = "ActiveActionStatus"
    completed_action_status: str = "CompletedActionStatus"
    failed_action_status: str = "FailedActionStatus"
    potential_action_status: str = "PotentialActionStatus"

class Action(BaseModel):
    type: Literal["Action"]
    name: str
    end_time: datetime
    start_time: datetime
    action_status: ActionStatusType
    agent: Agent
    error: Optional[str] = None
    instrument: Optional[Instrument] = None
    
class CreateAction(Action):
    type: Literal["CreateAction"]
    result: List[str]

class AssessAction(Action):
    type: Literal["AssessAction"]
    additional_type: str  

#
# Bagit classes
#

class BagitInfo(BaseModel):
    source_organization: str = Field(alias="Source-Organization")
    organization_address: str = Field(alias="Organization-Address")
    contact_name: str = Field(alias="Contact-Name")
    contact_email: str = Field(alias="Contact-Email")

#
# 
#

class CrateMeta(StrEnum):
    License: str = '<a href="https://opensource.org/license/mit">MIT License</a>'
    Publisher: str = '<a href="https://github.com/lsc-sde-crates">LSC SDE</a>'