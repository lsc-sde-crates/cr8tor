# Branching strategy

## Overview

We follow the branching strategy defined in latest Azure Devops best practises <https://learn.microsoft.com/en-us/azure/devops/repos/git/git-branching-guidance?view=azure-devops#use-feature-branches-for-your-work>. This methodology highly resembles Trunk-based development.

![branching strategy](https://learn.microsoft.com/en-us/azure/devops/repos/git/media/branching-guidance/featurebranching.png?view=azure-devops)

???+ warning
    ***main* branch is the PRODUCTION/LIVE version of the overall CR8TOR Solution!**

**main** branch has following restrictions:

- requires Pull Request
- source branches must be follow naming pattern: develop, feature/\*\*, release/\*\*, hotfix/\*\*, bugfix/\*\*

We allow using develop branch as the more stable dev related branch.

## Release strategy

We use `main` branch as the **PRODUCTION/LIVE** version. The release of newer version of cr8tor should involve a peer review session and approval from cr8tor repository admins.

Each DAR project repository has an Orchestrator workflow which uses reusable workflow from the cr8tor repository. By default, it **targets the cr8tor workflow** from the `main` branch.
![alt text](./../assets/screenshots/project_workflow_yaml.png)

If we want to test the DAR project using different branch or tag version, we need to amend the DAR project's Orchestrator workflow and the **target cr8tor workflow** as shown in above screenshot.
