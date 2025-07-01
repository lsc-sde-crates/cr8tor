# Publish Service

The **Publish Service** is responsible for the actual data transfer operations, handling data extraction from source systems, packaging for staging, and final publication to production storage. This service manages the complete data movement pipeline while maintaining security and integrity.

## Overview

The Publish Service is a FastAPI-based microservice that handles:

- Data extraction from source databases (SQL Server, MySQL, PostgreSQL, Databricks Unity Catalog)
- Data packaging and format conversion (DuckDB or csv format)
- Loading data to target database (PostgreSQL)
- Staging area management for data validation
- Production data publishing with integrity verification
- Hash calculation and BagIt packaging for data integrity

## Key Features

- **Multi-Source Data Extraction**: Support for various data source types
- **Format Conversion**: Converts data to standardized formats (DuckDB)
- **Staging Management**: Secure intermediate storage for data validation
- **Production Publishing**: Final data deployment to production storage
- **Integrity Verification**: Hash calculation and BagIt packaging
- **Pipeline Orchestration**: Coordinates complex data movement workflows

## Data Source Support

The Publish Service supports multiple source types for data extraction and processing:

### Databricks Unity Catalog

Primary integration with Databricks Unity Catalog providing:

- **Data Extraction**: Direct access to Databricks tables and views
- **Catalog-Level Support**: Browse catalogs, schemas, and tables
- **High-Performance Access**: Optimized for large-scale data operations

**Connection Parameters**:

- `host_url`: Databricks workspace URL
- `http_path`: SQL warehouse HTTP path
- `port`: Connection port (typically 443)
- `catalog`: Target catalog name

**Authentication Requirements**:

- Service Principal authentication via Azure Key Vault
- Required credential keys: `spn_clientid`, `spn_secret`

### SQL Databases

Support for various SQL database systems including:

- **PostgreSQL**: Open-source relational database
- **MySQL**: Popular open-source database system
- **Microsoft SQL Server**: Enterprise database system

**Connection Parameters**:

- `host_url`: Database server URL
- `database`: Database name to connect to
- `port`: Database connection port

**Authentication Requirements**:

- Username/password authentication via Azure Key Vault
- Required credential keys: `username_key`, `password_key`

**Supported Source Types**:

- `databrickssql` - Databricks Unity Catalog
- `postgresql` - PostgreSQL databases
- `mysql` - MySQL databases
- `mssql` / `sqlserver` - Microsoft SQL Server databases

## API Endpoints

### 1. Connection Validation

**Endpoint**: `POST /data-publish/validate`

Validates source and destination connections without transferring data.

**Purpose**:

- Tests connectivity to source and destination systems
- Validates authentication and permissions
- Confirms data extraction capabilities

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
  }
}
```

**Response Example**:

```json
{
  "status": "success",
  "payload": {
    "validation_status": "success"
  }
}
```

### 2. Data Packaging

**Endpoint**: `POST /data-publish/package`

Extracts data from source systems and packages it in staging storage.

**Purpose**:

- Extracts specified datasets from source systems
- Converts data to target format (DuckDB)
- Stores data in staging area for validation
- Returns staging location information

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
    "destination_type": "filestore",
    "data_retrieved": [
      {
        "file_path": "data/outputs/database.duckdb"
      }
    ]
  }
}
```

### 3. Data Publishing

**Endpoint**: `POST /data-publish/publish`

Moves data from staging to production storage with integrity verification.

**Purpose**:

- Transfers data from staging to production storage
- Calculates file hashes for integrity verification
- Creates BagIt packages for data preservation
- Returns production location and verification information

**Request Example**:

```json
{
  "project_name": "Pr004",
  "project_start_time": "20250205_010101",
  "destination": {
    "name": "LSC",
    "type": "filestore",
    "format": "duckdb"
  }
}
```

**Response Example**:

```json
{
  "status": "success",
  "payload": {
    "destination_type": "filestore",
    "data_published": [
      {
        "file_path": "production/data/outputs/database.duckdb",
        "hash_sha256": "abc123...",
        "size_bytes": 1048576
      }
    ]
  }
}
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TARGET_STORAGE_ACCOUNT_LSC_SDE_MNT_PATH` | `./outputs/lsc-sde` | LSC SDE storage mount path |
| `TARGET_STORAGE_ACCOUNT_NW_SDE_MNT_PATH` | `./outputs/nw-sde` | NW SDE storage mount path |
| `SECRETS_MNT_PATH` | `./secrets` | Path to mounted secrets folder |
| `DLTHUB_PIPELINE_WORKING_DIR` | `/home/appuser/dlt/pipelines` | DltHub working directory |

### Authentication

Required secrets for service operation:

**API Authentication**:

- `publishserviceapikey` - Service API key

**Data Source Authentication**:

**Databricks Unity Catalog**:

- `databricksspnclientid` - Databricks Service Principal client ID
- `databricksspnsecret` - Databricks Service Principal secret

**SQL Databases (PostgreSQL, MySQL, MSSQL)**:

- Database username keys - Configured via `username_key` in access credentials
- Database password keys - Configured via `password_key` in access credentials

**Storage Authentication**:

- Azure Storage Account keys (if using Azure storage)
- AWS credentials (if using AWS S3)
- Service Principal credentials for storage access

### OPAL Integration

Support for OPAL (Open Policy Agent Library) for:

- Policy-based data access controls
- Dynamic permission evaluation
- Audit logging and compliance
- Fine-grained access management
