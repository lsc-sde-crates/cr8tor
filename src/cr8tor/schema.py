from enum import StrEnum
from typing import List
from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime
from typing import Optional, Literal, Union

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
# Models for properties of ro-crate entities. Will have to expand on a needs basis 
#

class BaseRoCrateEntityProperties(BaseModel):
    
    id: str = Field(alias="@id", description="Mandatory identifier of entity. This needs to be unique within the context of the ro-crate knowledge graph")
    type: str = Field(alias="@type", description="Mandatory type of entity")
    description: Optional[str] = Field(description="Entity desc")
    
    class Config:
        allow_population_by_field_name = True

class OrganizationProps(BaseRoCrateEntityProperties):
    name: str = Field(description="Organisation name e.g. Lancaster University")
    url: HttpUrl = Field(description="Organisation URL")

class PersonProps(BaseRoCrateEntityProperties):
    name: str = Field(description="An individual's name")
    url: HttpUrl = Field(description="Organisation URL")

class SoftwareApplicationProps(BaseRoCrateEntityProperties):
    type: Literal["SoftwareApplication"] = Field(default="SoftwareApplication", alias="@type")
    name: str = Field(description="Software application name")
    provider: Union[OrganizationProps, PersonProps] = Field(description="Software provider. Can be organization or Person")

class SoftwareSourceCodeProps(BaseRoCrateEntityProperties):
    type: Literal["SoftwareSourceCode"] = Field(default="SoftwareSourceCode", alias="@type")
    name: str = Field(description="repo name")
    codeRepository: HttpUrl = Field(description="repo url")

class ActionProps(BaseRoCrateEntityProperties):
    type: Literal["Action"] = Field(default="Action", alias="@type")
    name: str = Field(description="Action name")
    start_time: datetime = Field(description="Start time of the action")
    end_time: datetime = Field(description="End time of the action")
    action_status: str = Field(description="Status of the action formmatted based on Provernance Crate Profile spec")
    agent: str = Field(description="The thing triggering the action i.e. a person, organisation or software application (e.g. Github Action)")
    error: Optional[str] = Field(default=None, description="Error output if action fails")
    instrument: Optional[str] = Field(default=None, description="Instrument performing the execution of the action (e.g. cr8tor, specific TRE service)")
    
class CreateActionProps(BaseRoCrateEntityProperties):
    type: Literal["CreateAction"] = Field(default="CreateAction", alias="@type")
    result: List[str] = Field(description="Id references to other data or context entities")

class AssessActionProps(BaseRoCrateEntityProperties):
    type: Literal["AssessAction"] = Field(default="AssessAction", alias="@type")
    additional_type: str = Field(description="Use to reference sub assessment actions (e.g. disclosure check)")

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