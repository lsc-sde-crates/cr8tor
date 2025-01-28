"""Functions to work with RO-Crate objects"""

import os
import uuid
from pathlib import Path
from typing import Annotated
from datetime import datetime

import bagit
import rocrate.model as m
import typer
from rocrate.rocrate import ROCrate

import cr8tor.core.schema as s
from cr8tor.exception import DirectoryNotFoundError
from cr8tor.utils import log, make_uuid
from cr8tor.cli.display import print_crate
from cr8tor.core.resourceops import (
    update_resource_entity,
    read_resource,
    create_resource_entity,
)

app = typer.Typer()


def init_bag(project_id: str, bag_dir: Path, config: dict) -> bagit.Bag:
    """
    Initializes a BagIt bag for a given project.
    Args:
        project_id (str): The unique identifier for the project.
        bag_dir (Path): The directory where the bag will be created.
        config (dict): Configuration dictionary containing BagIt metadata.
    Returns:
        bagit.Bag: The created BagIt bag object.
    Raises:
        OSError: If the directory cannot be created.
        bagit.BagError: If there is an error creating the bag.
    """

    bag_dir.mkdir(parents=True, exist_ok=True)

    bag: bagit.Bag = bagit.make_bag(bag_dir=bag_dir, checksums=["sha512"])

    # bag.info.update(s.BagitInfo(**config["bagit-info"])) # ToDo: Fix serialisation alias issue
    bag.info.update(**config["bagit-info"])
    bag.info["External-Identifier"] = make_uuid(project_id)

    return bag


def check_required_keys(data: dict, required_keys: dict):
    for key, error_message in required_keys.items():
        if key not in data:
            raise KeyError(error_message)


@app.command(name="create")
def create(
    resources_dir: Annotated[
        Path,
        typer.Option(
            default="-i", help="Directory containing resources to include in RO-Crate."
        ),
    ] = "./resources",
    config_file: Annotated[
        Path, typer.Option(default="-c", help="Location of configuration TOML file.")
    ] = "./config.toml",
    dryrun: Annotated[bool, typer.Option(default="--dryrun")] = False,
):
    """
    Create a 5-Safes Research Object Crate (RO-Crate) from the specified resources directory.
    This function generates an RO-Crate by loading project and dataset metadata from YAML files
    located in the provided resources directory. The crate is populated with project information,
    governance details, and dataset metadata, and then packaged as a BagIt Archive in the "bagit/" directory.

    If the `dryrun` argument is provided, the function will print the crate details without writing to the "crate/" directory.

    Example:
        $ cr8tor create -i /path/to/resources
    """
    create_start_dt = datetime.now()
    project_uuid: Annotated[
        str,
        "Project UUID is a unique auto-generated identifier on creation of the project",
    ] = os.getenv("PROJECT_UUID", str(uuid.uuid4()))

    if not resources_dir.exists():
        raise DirectoryNotFoundError(resources_dir)

    project_resource_path = resources_dir.joinpath("governance", "project.toml")
    governance = read_resource(project_resource_path)

    if "project" not in governance:
        raise KeyError(
            f"To create a LSC project, 'project' properties must be defined in resource: {project_resource_path}"
        )

    governance["project"].setdefault("id", project_uuid)

    update_resource_entity(project_resource_path, "project", governance["project"])

    create_action_props = s.CreateActionProps(
        id=f"create-project-action-{project_uuid}",
        name="Create LSC Project Action",
        start_time=create_start_dt,
        end_time=datetime.now(),
        action_status="CompletedActionStatus",
        agent="GitHub Action",  # need to add agent to command line
        error=None,
        instrument="cr8tor",
        result=["foo"],
    )

    create_resource_entity(project_resource_path, "actions", [])
    update_resource_entity(project_resource_path, "actions", create_action_props.dict())

    build(resources_dir, config_file, dryrun)


@app.command(name="build")
def build(
    resources_dir: Annotated[
        Path,
        typer.Option(
            default="-i", help="Directory containing resources to include in RO-Crate."
        ),
    ] = "./resources",
    config_file: Annotated[
        Path, typer.Option(default="-c", help="Location of configuration TOML file.")
    ] = "./config.toml",
    dryrun: Annotated[bool, typer.Option(default="--dryrun")] = False,
):
    ###############################################################################
    # 1 Validate project build materials (i.e. resources/ & config.toml)
    ###############################################################################

    config = read_resource(config_file)

    if not resources_dir.exists():
        raise DirectoryNotFoundError(resources_dir)

    project_resource_path = resources_dir.joinpath("governance", "project.toml")
    governance = read_resource(project_resource_path)

    access_resource_path = resources_dir.joinpath("access", "access.toml")
    access = read_resource(access_resource_path)

    ###############################################################################
    # 2 Check mandatory user-defined elements (i.e. gov, access) exists before
    #  pydantic model validation on fields
    ###############################################################################

    governance_required_keys = {
        "project": f"To build ro-crate 'project' properties must be defined in resource: {project_resource_path}",
        "requesting_agent": f"To build ro-crate 'requesting_agent' properties must be defined in resource: {project_resource_path}",
        "repository": f"To build ro-crate 'repository' properties must be defined in resource: {project_resource_path}",
        "actions": f"To build ro-crate 'actions'list property must be defined in resource: {project_resource_path}",
    }

    access_required_keys = {
        "source": f"To build ro-crate source connection info is needed in resource: {access_resource_path}",
        "credentials": f"To build ro-crate connection credentials info is needed in resource: {access_resource_path}",
    }

    check_required_keys(governance, governance_required_keys)
    check_required_keys(access, access_required_keys)

    ###############################################################################
    # 3 Create initial Ro-Crate & build contextual entities
    ###############################################################################

    crate = ROCrate(gen_preview=True)

    #
    # Load project info and init RC 'Project' entity
    #

    project_props = s.ProjectProps(**governance["project"])
    log.info(
        f"[cyan]Creating RO-Crate for[/cyan] - [bold magenta]{project_props.name}[/bold magenta]",
    )

    project_entity = m.ContextEntity(
        crate=crate,
        identifier=project_props.id,
        properties={
            "@type": "Project",
            "name": project_props.name,
            "identifier": project_props.reference,
        },
    )

    crate.add(project_entity)

    #
    # Load requesting agent info and init RC 'Person' entity
    #

    requesting_agent_props = s.RequestingAgentProps(**governance["requesting_agent"])
    person_entity = m.Person(
        crate,
        identifier=f"requesting-agent-{project_props.id}",
        properties={
            "name": requesting_agent_props.name,
            "affiliation": {"@id": f"requesting-agent-org-{project_props.id}"},
        },
    )

    aff_entity = m.ContextEntity(
        crate,
        identifier=f"requesting-agent-org-{project_props.id}",
        properties={
            "@type": "Organisation",
            "name": requesting_agent_props.affiliation.name,
            "url": str(requesting_agent_props.affiliation.url),
        },
    )

    crate.add(aff_entity)
    crate.add(person_entity)

    # Relation definition for ro-crate metadata file only (i.e. not stored are managed in the resources)
    project_entity["memberOf"] = [{"@id": person_entity.id}]

    # Update resources to include generated id properties for project info
    # update_resource_entity(project_resource_path, "project", project_props.dict())

    #
    # Load project repository info and init RC 'SoftwareSourceCode' entity
    #

    repo_props = s.SoftwareSourceCodeProps(**governance["repository"])

    repo_entity = m.ContextEntity(
        crate=crate,
        identifier=f"repo-{project_props.id}",
        properties={
            "@type": "SoftwareSourceCode",
            "name": repo_props.name,
            "description": repo_props.description,
            "codeRepository": f"{repo_props.codeRepository}cr8-{project_props.id}",
        },
    )

    crate.add(repo_entity)
    crate.metadata["isBasedOn"] = {"@id": f"repo-{project_props.id}"}

    #
    # Load access info and init RC entities
    #

    contract_props = s.DataAccessContract(
        connection=s.DatabricksSourceConnection(**access["source"]),
        credentials=s.SourceAccessCredential(**access["credentials"]),
    )
    # TODO: Identify and init any RC contextual entities for describing data access

    ###############################################################################
    # 4 Build data entities
    ###############################################################################

    #
    # Governance resources
    #

    crate.add_file(
        source=project_resource_path,
        dest_path="governance/project.toml",
        properties={
            "name": project_props.name,
            "description": project_props.description,
        },
    )

    log.info(
        msg="[cyan]Validated and added file[/cyan] - [bold magenta]governance/project.toml[/bold magenta]",
    )

    #
    # Dataset metadata resources
    #

    for f in resources_dir.joinpath("metadata").glob("dataset*.toml"):
        dataset_dict = read_resource(f)
        dataset_props = s.DatasetMetadata(**dataset_dict)

        crate.add_file(
            source=f,
            dest_path=f"metadata/{f.name}",
            properties={
                "name": dataset_props.name,
                "description": dataset_props.description,
            },
        )

        log.info(
            msg=f"[cyan]Validated and added datasets descriptor files[/cyan] - [bold magenta]metadata/{f.name}[/bold magenta]",
        )

    #
    # Access resources
    #

    crate.add_file(
        source=project_resource_path,
        dest_path="access/access.toml",
        properties={"name": contract_props.connection.name},
    )

    log.info(
        msg="[cyan]Validated and added access descriptor file[/cyan] - [bold magenta]access/access.toml[/bold magenta]",
    )

    ###############################################################################
    # 5 Finalise Crate
    ###############################################################################
    crate.name = project_props.name
    crate.description = project_props.description
    crate.license = s.CrateMeta.License
    crate.publisher = m.ContextEntity(
        crate,
        identifier=s.CrateMeta.Publisher,
        properties={
            "@type": "Organisation",
            "name": "LSC SDE",
            "url": repo_props.codeRepository,
        },
    )
    crate.mainEntity = project_entity

    ###############################################################################
    # 6 Process and render all action entities
    ###############################################################################

    #
    # Check for actions
    #

    for action in governance["actions"]:
        if action["type"] == "CreateAction":
            action_props = s.CreateActionProps(**action)
        elif action["type"] == "AssessAction":
            action_props = s.AssessActionProps(**action)

        crate.add_action(
            instrument=action_props.instrument,
            identifier=action_props.id,
            # object={"@id": "https://example.com/dataset"},
            # result={"@id": "https://example.com/result"},
            properties={
                "name": action_props.name,
                "startTime": action_props.start_time.isoformat(),
                "endTime": action_props.end_time.isoformat(),
                "actionStatus": action_props.action_status,
                "agent": {
                    "@id": "foo",
                    "@type": "SoftwareApplication",
                    "name": "GitHub Action",
                },  # TODO ADD AGENT ENTITY
            },
        )

    ###############################################################################
    # 7 Add Ro-crate meta to bagit directory structure
    ###############################################################################
    if not dryrun:
        bag_dir = Path("./bagit")

        if bag_dir.exists() and bag_dir.is_dir():
            bag = bagit.Bag(str(bag_dir))

            # Update bag info from config.toml; This does not modify the External-Identifier.
            # Delete and recreate the bag if the External-Identifier needs to be changed.
            bag.info.update(**config["bagit-info"])
            log.info("Loaded existing bag")
        else:
            bag = init_bag(project_id=project_props.id, bag_dir=bag_dir, config=config)

        crate.write(bag_dir / "data")
        bag.save(manifests=True)

        n_payload_files = len(list(bag.payload_files()))
        log.info(
            f"[cyan]RO-Crate BagIt created at[/cyan] - [bold magenta]{bag_dir} with {n_payload_files} files.[/bold magenta]",
        )
    else:
        log.warning(
            "[bold red]Dry run option set. Crate will not be written to disk.[/bold red]\n"
        )

    print_crate(crate=crate)


###############################################################################
# VALIDATE: Semantic validation of resources info (e.g. data contract details)
###############################################################################


@app.command(name="validate")
def validate(
    bagit_dir: Annotated[
        Path,
        typer.Option(
            default="-i", help="Bagit directory containing RO-Crate data directory"
        ),
    ] = "./bagit",
    resources_dir: Annotated[
        Path,
        typer.Option(
            default="-i", help="Directory containing resources to include in RO-Crate."
        ),
    ] = "./resources",
):
    project_resource_path = resources_dir.joinpath("governance", "project.toml")
    proj_roc_meta_path = bagit_dir.joinpath("data")

    #
    # Verify mircroservice in target TRE can connect to data source (i.e. verify data contract details in access/)
    # Call REST API - Talk to Piotr about what this will look like
    #

    #
    # Query ro-crate metadata to ensure prereq actions have completed
    # Given its a knowledge graph we should probably be using something like rdflib to load metadata into a graph and query using SPARQL
    #

    crate = ROCrate(proj_roc_meta_path)

    assess_action_props = s.AssessActionProps(
        id="validate-action-XYZ",
        name="Validate Assess Action",
        start_time=datetime.now(),
        end_time=datetime.now(),
        action_status="CompletedActionStatus",
        agent="GitHub Action",
        error=None,
        instrument="cr8tor",
        result=["Bar"],
        additional_type="Semantic Validation",
    )

    crate.add_action(
        instrument=assess_action_props.instrument,
        identifier=assess_action_props.id,
        # object={"@id": "https://example.com/dataset"},
        # result={"@id": "https://example.com/result"},
        properties={
            "name": assess_action_props.name,
            "startTime": assess_action_props.start_time.isoformat(),
            "endTime": assess_action_props.end_time.isoformat(),
            "actionStatus": assess_action_props.action_status,
            "agent": {
                "@id": "foo",
                "@type": "SoftwareApplication",
                "name": "GitHub Action",
            },  # TODO ADD AGENT ENTITY
        },
    )

    update_resource_entity(project_resource_path, "actions", assess_action_props.dict())

    build(resources_dir)


@app.command(name="approve")
def approve(
    bagit_dir: Annotated[
        Path,
        typer.Option(
            default="-i", help="Bagit directory containing RO-Crate data directory"
        ),
    ] = "./bagit",
    resources_dir: Annotated[
        Path,
        typer.Option(
            default="-i", help="Directory containing resources to include in RO-Crate."
        ),
    ] = "./resources",
    agent_token: Annotated[
        str,
        typer.Option(default="-i", help=""),
    ] = "./resources",
):
    project_resource_path = resources_dir.joinpath("governance", "project.toml")
    proj_roc_meta_path = bagit_dir.joinpath("data")

    #
    # Authorise approver agent
    #

    #
    # Check previous prereq actions have been performed
    #

    #
    # Handle different REST responses from GA on approval process to create/update action status
    #

    approve_action_props = s.AssessActionProps(
        id="apporove-assess-action-XYZ",
        name="approve-Assess Action Test",
        start_time=datetime.now(),
        end_time=datetime.now(),
        action_status="CompletedActionStatus",
        agent="Joe Bloggs",
        error=None,
        instrument="cr8tor",
        result=["Bar"],
        additional_type="Sign Off Approval",
    )

    crate = ROCrate(proj_roc_meta_path)

    crate.add_action(
        instrument=approve_action_props.instrument,
        identifier=approve_action_props.id,
        # object={"@id": "https://example.com/dataset"},
        # result={"@id": "https://example.com/result"},
        properties={
            "name": approve_action_props.name,
            "startTime": approve_action_props.start_time.isoformat(),
            "endTime": approve_action_props.end_time.isoformat(),
            "actionStatus": approve_action_props.action_status,
            "agent": {
                "@id": "foo",
                "@type": "SoftwareApplication",
                "name": "GitHub Action",
            },  # TODO ADD AGENT ENTITY
        },
    )

    update_resource_entity(
        project_resource_path, "actions", approve_action_props.dict()
    )

    build(resources_dir)


@app.command(name="publish")
def publish(
    bagit_dir: Annotated[
        Path,
        typer.Option(
            default="-i", help="Bagit directory containing RO-Crate data directory"
        ),
    ] = "./bagit",
    resources_dir: Annotated[
        Path,
        typer.Option(
            default="-i", help="Directory containing resources to include in RO-Crate."
        ),
    ] = "./resources",
    agent_token: Annotated[
        str,
        typer.Option(default="-i", help=""),
    ] = "./resources",
):
    # project_resource_path = resources_dir.joinpath("governance", "project.toml")
    # proj_roc_meta_path = bagit_dir.joinpath("data")

    #
    # Log the action and update on statuses
    #

    build(resources_dir)
