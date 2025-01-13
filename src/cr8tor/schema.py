from enum import StrEnum
from typing import List

from pydantic import BaseModel, Field


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


class Requester(BaseModel):
    """
    The individual person who is requesting the run MUST be indicated as an `agent` from the
    `CreateAction`, which SHOULD have an `affiliation` to the organisation they are representing
    for access control purposes

    https://trefx.uk/5s-crate/0.5-DRAFT/#requesting-agent
    """

    name: str
    affiliation: str
    #memberOf: List[str]


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
