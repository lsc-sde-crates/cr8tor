# Branching strategy

## Overview

We follow the branching strategy defined in latest Azure Devops best practises <https://learn.microsoft.com/en-us/azure/devops/repos/git/git-branching-guidance?view=azure-devops#use-feature-branches-for-your-work>. This methodology highly resembles Trunk-based development.

![branching strategy](https://learn.microsoft.com/en-us/azure/devops/repos/git/media/branching-guidance/featurebranching.png?view=azure-devops)

???+ warning
    ***main* branch is the PRODUCTION/LIVE version for the overall CR8TOR Solution!**

**main** branch has following restrictions:

- requires Pull Request

## Release strategy

For cookie-cutter we do not use any GitHub Releases or Deployment or Packages.
The latest version of code commited to the 'main' branch will be used by the cr8tor as a template bases for a DAR project's repository.
