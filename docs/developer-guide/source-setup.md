# Source setup

Cr8tor Solution supports multiple source data types including Databricks Unity Catalog and various SQL databases. The cr8tor publisher microservices (metadata-service and publish-service) can work with different source types.

## Supported Source Types

The following source types are currently supported:

- **DatabricksSQL** - Databricks Unity Catalog
- **PostgreSQL** - PostgreSQL databases
- **MySQL** - MySQL databases
- **MSSQL** - Microsoft SQL Server databases

Each source type has different connection parameters and credential requirements as detailed below.

## Databricks Unity Catalog

If Databricks Unity Catalog is the source dataset, this will be recognised in Metadata and Publish Services as `databrickssql` type in [DAR project access file](./../user-guide/update-resources-files.md#accessaccess).

Connection to Databricks Unity Catalog is made with Databricks Workspace Service principal.
[See here how to set up the SPN, add secrets and grant relevant access and permissions.](https://github.com/lsc-sde-crates/cr8tor-publisher/blob/main/docs/services.md#databricks-service-principal)

### Databricks Connection Parameters

- `host_url`: Databricks workspace URL (e.g., `https://<workspace>.azuredatabricks.net`)
- `http_path`: SQL warehouse HTTP path (e.g., `/sql/1.0/warehouses/<warehouse-id>`)
- `port`: Connection port (default: 443)
- `catalog`: Databricks Unity Catalog name

### Databricks Credential Requirements

Databricks sources use Service Principal authentication and require the following credential keys:

- `spn_clientid`: Key name in secrets provider containing the Service Principal client ID
- `spn_secret`: Key name in secrets provider containing the Service Principal secret

## SQL Databases (PostgreSQL, MySQL, MSSQL)

SQL database sources are recognised in Metadata and Publish Services by their respective types: `postgresql`, `mysql`, `mssql`, or `sqlserver`.

### SQL Database Connection Parameters

- `host_url`: Database server URL (e.g., `mysql-server.example.com`)
- `database`: Database name to connect to
- `port`: Database connection port (varies by database type)

### SQL Database Credential Requirements

SQL database sources use username/password authentication and require the following credential keys:

- `username_key`: Key name in secrets provider containing the database username
- `password_key`: Key name in secrets provider containing the database password

## Credential Configuration Examples

### Databricks Unity Catalog Example

```toml
[source]
type = "databrickssql"
host_url = "https://workspace.azuredatabricks.net"
http_path = "/sql/1.0/warehouses/warehouse-id"
port = 443
catalog = "my_catalog"

[credentials]
provider = "AzureKeyVault"
spn_clientid = "databricks-spn-client-id-secret"
spn_secret = "databricks-spn-secret-secret"
```

### PostgreSQL Example

```toml
[source]
type = "postgresql"
host_url = "postgres-server.example.com"
database = "my_database"
port = 5432

[credentials]
provider = "AzureKeyVault"
username_key = "postgres-username-secret"
password_key = "postgres-password-secret"
```

### MySQL Example

```toml
[source]
type = "mysql"
host_url = "mysql-server.example.com"
database = "my_database"
port = 3306

[credentials]
provider = "AzureKeyVault"
username_key = "mysql-username-secret"
password_key = "mysql-password-secret"
```

### MSSQL Example

```toml
[source]
type = "mssql"
host_url = "mssql-server.example.com"
database = "my_database"
port = 1433

[credentials]
provider = "AzureKeyVault"
username_key = "mssql-username-secret"
password_key = "mssql-password-secret"
```
