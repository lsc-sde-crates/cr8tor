# Source setup

Cr8tor Solution supports Databricks Unity Catalog as the primary source data type but this could evolve in future.

## Databricks Unity Catalog

If Databricks Unity Catalog is the source dataset, this will be recognised in Metadata and Publish Services as DatabricksSQL type in [DAR project access file](./../user-guide/update-resources-files.md#accessaccess).

Connection to Databricks Unity Catalog is made with Databricks Workspace Service principal.
[See here how to set up the SPN, add secrets and grant relevant access and permissions.](https://github.com/lsc-sde-crates/cr8tor-publisher/blob/main/docs/services.md#databricks-service-principal)
