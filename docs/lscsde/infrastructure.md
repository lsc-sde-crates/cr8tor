# Infrastructure

## Overview

Lancashire and Cumbria SDE uses Azure for hosting resources required to run Cr8tor Publisher microservices:

- Azure Keyvault
    1. to store API-keys for Approval, Metadata and Publish service endpoints; 2. to store connection details to source and target systems e.g. Databricks Service Principal secrets;
    2. secrets are mounted to kubernetes containers;

- Storage Accounts
    1. to store the extracted data.
    2. two containers:
        1. staging - to store the raw extract,
        2. production - to store the final data files (e.g. without any DLTHub log files).
    3. separate storage accounts per target organisation;
        1. one for LSC,
        2. one for NW.

- Azure Data Share
    1. to safely serve data to trused organisations,
    2. created to share 'production' container of NW Storage account with the North West Azure Data Share
    3. invitation can be shared using IAC (there is a Bicep code for that).

- Private endpoints.
    1. used to connect Kubernetes to Storage Accounts in a safe way

The Configuration and Release documentation for these resources [can be found here](https://github.com/lsc-sde/DataPlatform-Infrastructure/blob/develop/readme.md).
