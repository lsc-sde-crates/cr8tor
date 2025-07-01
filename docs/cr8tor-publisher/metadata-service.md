# Metadata Service

The **Metadata Service** is responsible for validating dataset definitions and retrieving metadata from data sources without exposing the actual data. It ensures that the metadata specified in data access requests is accurate and available.

## Overview

The Metadata Service is a FastAPI-based microservice that specializes in:

- Validating source and destination connections
- Retrieving schema information from data sources (e.g., Databricks Unity Catalog)
- Providing table and column metadata including descriptions, data types, and names
- Ensuring metadata accuracy without data exposure

## Key Features

- **Connection Validation**: Tests connectivity to source and destination systems
- **Schema Retrieval**: Fetches comprehensive metadata from data catalogs
- **Data Type Mapping**: Provides standardized data type information
- **Security-First Design**: Accesses only metadata, never actual data
- **Databricks Integration**: Native support for Databricks Unity Catalog
- **Flexible Source Support**: Extensible architecture for multiple data source types

## API Endpoints

### POST /metadata/project

The primary endpoint for metadata operations.

**Purpose**:

- Validates source database connections
- Retrieves metadata for requested datasets
- Returns comprehensive schema information

**Request Example**:

```json
{
  "project_name": "Pr004",
  "project_start_time": "20250205_010101",
  "destination": {
    "name": "LSC",
    "type": "filestore",
    "format": "duckdb"
  },
  "source": {
    "type": "databrickssql",
    "host_url": "https://my-databricks-workspace.azuredatabricks.net",
    "http_path": "/sql/1.0/warehouses/bd1395d4652aa599",
    "port": 443,
    "catalog": "catalog_name",
    "credentials": {
      "provider": "AzureKeyVault",
      "spn_clientid": "databricksspnclientid",
      "spn_secret": "databricksspnsecret"
    }
  },
  "dataset": {
    "schema_name": "example_schema_name",
    "tables": [
      {
        "name": "person",
        "columns": [
          {"name": "person_key"},
          {"name": "person_id"},
          {"name": "age"}
        ]
      },
      {
        "name": "address",
        "columns": [
          {"name": "address_key"},
          {"name": "address"}
        ]
      }
    ]
  }
}
```

**Response Example**:

```json
{
  "status": "success",
  "payload": {
    "validation_status": "success",
    "metadata": {
      "schema_name": "example_schema_name",
      "tables": [
        {
          "name": "person",
          "description": "Person demographics table",
          "columns": [
            {
              "name": "person_key",
              "data_type": "bigint",
              "description": "Unique person identifier",
              "nullable": false
            },
            {
              "name": "person_id",
              "data_type": "string",
              "description": "Person ID from source system",
              "nullable": true
            },
            {
              "name": "age",
              "data_type": "int",
              "description": "Person age in years",
              "nullable": true
            }
          ]
        }
      ]
    }
  }
}
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRETS_MNT_PATH` | `./secrets` | Path to mounted secrets folder |
| `ENVIRONMENT` | `local` | Environment variable |

### Authentication

The service requires the following secrets for operation:

**Required Secrets**:

- `metadataserviceapikey` - API key for service authentication

## Data Source Support

The Metadata Service supports multiple source types for extracting metadata:

### Databricks Unity Catalog

Primary integration with Databricks Unity Catalog providing:

- **Catalog-Level Access**: Browse catalogs, schemas, and tables
- **Column Metadata**: Data types, descriptions, and constraints

**Connection Parameters**:

- `host_url`: Databricks workspace URL
- `http_path`: SQL warehouse HTTP path
- `port`: Connection port (typically 443)
- `catalog`: Target catalog name

**Authentication Methods**:

- Service Principal authentication via Azure Key Vault

**Required Secrets**:

- Databricks Service Principal client ID. Provide secret name, e.g. *databricksspnclientid* under `spn_clientid` key in access credentials input
- Databricks Service Principal secret. Provide secret name, e.g. *databricksspnsecret* under `spn_secret` key in access credentials input

### SQL Databases

Support for various SQL database types including:

- **PostgreSQL**: Open-source relational database
- **MySQL**: Popular open-source database system
- **Microsoft SQL Server**: Enterprise database system

**Connection Parameters**:

- `host_url`: Database server URL
- `database`: Database name to connect to
- `port`: Database connection port

**Authentication Methods**:

- Username/password authentication via Azure Key Vault

**Required Secrets**:

- Database username. Provide secret name under `username_key` in access credentials input
- Database password. Provide secret name under `password_key` in access credentials input

**Supported Source Types**:

- `postgresql` - PostgreSQL databases
- `mysql` - MySQL databases
- `mssql` / `sqlserver` - Microsoft SQL Server databases
