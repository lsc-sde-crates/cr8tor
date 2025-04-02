# Overview

![alt text](https://github.com/lsc-sde-crates/cr8tor-publisher/blob/main/docs/architecture.png?raw=true)

Cr8tor Publisher is made up of three microservices which facilitate cr8tor Data Access Requests, enabling users to request, approve, and retrieve datasets securely and efficiently:

1. Approval Service - acts as an API gateway, taking the requests from the outside world and forwarding them to the relevant service. [See detail docs for Approval Service](https://github.com/lsc-sde-crates/cr8tor-publisher/blob/main/approval-service/docs/service.md).

2. Metadata Service - fetches the dataset's metadata, like table-column level descriptions, data types, names. [See detail docs for Metadata Service](https://github.com/lsc-sde-crates/cr8tor-publisher/blob/main/metadata-service/docs/service.md).

3. Publish Service - retrieves the dataset, packages in requested format and publishes to target destination. [See detail docs for Publish Service](https://github.com/lsc-sde-crates/cr8tor-publisher/blob/main/publish-service/docs/service.md).

The Microservices are based on Docker container. They can be deployed to any Kubernetes service like Azure Kubernetes Service (AKS) that supports mounting volumes.

???+ note
    For example, Lancashire and Cumbria Secure Data Enviornment department uses Azure Kubernetes to host and run the Microservices within their SDE enviornment. The specific Infrastructure and Kubernetes (K8S) configuration [can be found here](https://github.com/lsc-sde-crates/cr8tor-publisher/blob/main/docs/services.md#installation-onto-kubernetes).
