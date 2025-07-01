# Approval Service

The **Approval Service** acts as an API gateway for the CR8TOR Publisher platform, providing a centralized entry point for all data access requests and orchestrating communication between the Metadata and Publish Services.

## Overview

The Approval Service is a FastAPI-based microservice that serves as the main interface between the CR8TOR CLI and the underlying data processing services. It handles request validation, authentication, and routing while providing a consistent API interface.

## Key Features

- **API Gateway Functionality**: Central routing point for all CR8TOR operations
- **Request Validation**: Validates incoming requests before forwarding to appropriate services
- **Service Orchestration**: Coordinates between Metadata and Publish Services
- **Authentication Management**: Handles API key-based authentication
- **Error Handling**: Provides consistent error responses and logging
- **Response Formatting**: Standardizes response formats across services

## API Endpoints

### 1. Project Validation

**Endpoint**: `POST /project/validate`

Forwards validation requests to both Metadata and Publish Services to validate connections and retrieve dataset metadata.

**Purpose**:

- Validates source and destination connections
- Retrieves metadata for requested datasets
- Ensures data availability before proceeding with staging

**Request Flow**:

1. Receives validation request from CR8TOR CLI
2. Forwards request to Metadata Service for schema validation
3. Forwards request to Publish Service for connection validation
4. Aggregates responses and returns metadata information

### 2. Data Packaging

**Endpoint**: `POST /project/package`

Forwards packaging requests to the Publish Service to extract and stage data.

**Purpose**:

- Initiates data extraction from source systems
- Packages data in staging storage
- Returns staging location information

**Request Flow**:

1. Receives packaging request from CR8TOR CLI
2. Forwards request to Publish Service for data extraction
3. Returns staging details including file paths and formats

### 3. Data Publishing

**Endpoint**: `POST /project/publish`

Forwards publishing requests to the Publish Service to move data to production storage.

**Purpose**:

- Moves data from staging to production storage
- Calculates hash values for integrity verification
- Provides final data location information

**Request Flow**:

1. Receives publishing request from CR8TOR CLI
2. Forwards request to Publish Service for production deployment
3. Returns production details including file paths and hash values

## Configuration

### Environment Variables

The Approval Service requires the following environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `METADATA_CONTAINER_NAME` | `metadata-container` | Name of the Docker container for Metadata service |
| `METADATA_CONTAINER_PORT` | `8002` | Port of Metadata container exposed to other services |
| `PUBLISH_CONTAINER_NAME` | `publish-container` | Name of the Docker container for Publish service |
| `PUBLISH_CONTAINER_PORT` | `8003` | Port of Publish container exposed to other services |
| `SECRETS_MNT_PATH` | `./secrets` | Path to the folder where secrets are mounted |

### Authentication

The service uses static API key authentication requiring the following secrets:

**Required Secrets**:

- `approvalserviceapikey` - API key for accessing the Approval Service
- `metadataserviceapikey` - API key for calling the Metadata Service
- `publishserviceapikey` - API key for calling the Publish Service

When working locally, secret files should be stored under the `SECRETS_MNT_PATH` folder. In production, secrets are typically managed through Azure Key Vault or similar secret management systems.

## Docker Configuration

### Docker Network

The Approval Service communicates with other services through Docker networking. Ensure all services are on the same Docker network for proper inter-service communication.

### Container Communication

Services communicate using container names and internal ports:

- Metadata Service: `http://metadata-container:8002`
- Publish Service: `http://publish-container:8003`
