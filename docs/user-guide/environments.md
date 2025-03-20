# Environments

## Overview

Cr8tor cli app and Cr8tor-Publisher app are designed to extract the data from different source environments: DEV, TEST and PROD.

When creating a new DAR project, we can choose the environment we want to work with. This will drive the GitHub runners and set of Organisation secrets that will be used during the main Orchestrator workflow run.

As an example, choosing the DEV environment at the project level will pass the argument to the Orchestrator workflow. It will select the APPROVALS_API_TOKEN_DEV and APPROVAL_HOST_DEV secrets dedicated to that environment. Additionally, it will choose the runner dev-vm-01 (dev-cr8tor-vm), which can connect to the Databricks Unity Catalog within the dev-dedicated virtual network.

![cr8tor workflow environment options](./../assets/screenshots/cr8tor_workflow_environments.png)

Example of cr8tor workflow environment use:
![cr8tor workflow environment use](./../assets/screenshots/cr8tor_orchestrator_env_use.png)

Organisation secrets:
![organisation secrets for approval service](./../assets/screenshots/organisation_environments_secrets.png)

Organisation runner:
![organisation runners](./../assets/screenshots/organisation_runners.png)
