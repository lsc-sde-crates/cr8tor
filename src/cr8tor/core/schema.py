"""Pydantic models to validate properties of schema.org entities and other resources that will go within the RO-Crate"""

from enum import StrEnum
from typing import List, Optional

from pydantic import BaseModel, Field

###############################################################################
# Models to validate properties of Schema.org entities
###############################################################################

# Pydantic model names should follow the convention of ThingProps eg. PersonProps
# Where one of the properties is a reference to another schema.org entity,
# this should be of type Any or str and optional, rather than a reference to the ThingProps of that entity
# For instance, Person may have an affiliation property. This should not be of type AffiliationProps.


class ProjectProps(BaseModel):
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


class CodeRepositoryProps(BaseModel):
    """
    External Github repository used to manage this LSCSDE project
    """

    name: str
    description: str
    url: str


class AffiliationProps(BaseModel):
    name: str
    url: str


class RequestingAgentProps(BaseModel):
    """
    The individual person who is requesting the run MUST be indicated as an `agent` from the
    `CreateAction`, which SHOULD have an `affiliation` to the organisation they are representing
    for access control purposes

    https://trefx.uk/5s-crate/0.5-DRAFT/#requesting-agent
    """

    name: str
    affiliation: AffiliationProps  # Mike to look at whether we should keep this pattern. Risks circular deps.


###############################################################################
# Models to validate other entities that are unrelated to Schema.org entities
###############################################################################


class ProjectInit(BaseModel):
    project_name: str = Field(default="CR8TOR Demo Project")
    project_description: Optional[str]
    requester: Optional[str] = ""
    requester_affiliation: Optional[str] = ""
    requester_affiliation_url: Optional[str] = ""
    timestamp: Optional[str] = ""


class CrateMeta(StrEnum):
    License: str = '<a href="https://opensource.org/license/mit">MIT License</a>'
    Publisher: str = '<a href="https://github.com/lsc-sde-crates">LSC SDE</a>'


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
