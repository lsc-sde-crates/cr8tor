# CR8TOR CLI Commands Reference

CR8TOR CLI provides a comprehensive set of commands to manage the entire data access request (DAR) lifecycle, from project initiation to data publication.

## Core Workflow Commands

### Initiate Project

:::cr8tor.cli.initiate.initiate

???+ warning

    **--push** argument requires a fine-grained PAT token generated in GitHub. It must be stored under local environment variable GH_TOKEN. See [minimum PAT token permissions defined here](./../developer-guide/orchestration-layer-setup.md#github-pat-token).

### Create Project RO-Crate

:::cr8tor.cli.create.create

### Build RO-Crate Package

:::cr8tor.cli.build.build

### Validate Project Metadata

:::cr8tor.cli.validate.validate

## Approval Workflow Commands

### Sign-Off Project

:::cr8tor.cli.sign_off.sign_off

### Disclosure Check

:::cr8tor.cli.disclosure.disclosure

## Data Transfer Commands

### Stage Data Transfer

:::cr8tor.cli.stage_transfer.stage_transfer

### Publish Data

:::cr8tor.cli.publish.publish

## Command Workflow

The CR8TOR commands follow a specific sequence in the data access workflow:

1. **initiate** - Creates a new DAR project repository from cookiecutter template
2. **create** - Initializes the project with unique identifiers and basic metadata
3. **build** - Builds the BagIt RO-Crate package containing project metadata
4. **validate** - Validates data source connections and retrieves metadata
5. **sign-off** - Records approval for the validated data request
6. **stage-transfer** - Transfers data from source to staging storage
7. **disclosure** - Records disclosure approval for staged data
8. **publish** - Moves data from staging to production storage

???+ info "Command Dependencies"

    Each command typically depends on the successful completion of previous commands in the workflow. The CLI validates these dependencies and will exit with an error if prerequisite steps are missing.
