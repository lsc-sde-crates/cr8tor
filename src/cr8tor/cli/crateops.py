"""Functions to work with RO-Crate objects"""

import os
import uuid
from pathlib import Path
from typing import Annotated

import bagit
import rocrate.model as m
import typer
from rocrate.rocrate import ROCrate

import cr8tor.core.schema as s
from cr8tor.exception import DirectoryNotFoundError
from cr8tor.utils import log, make_uuid
from cr8tor.cli.display import print_crate
from cr8tor.cli.resourceops import update_resource_entity, read_resource

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
        "project": f"To create a LSC project, 'project' properties must be defined in resource: {project_resource_path}",
        "requesting_agent": f"To create a LSC project, 'requesting_agent' properties must be defined in resource: {project_resource_path}",
        "repository": f"To create a LSC project, 'repository' properties must be defined in resource: {project_resource_path}",
    }

    access_required_keys = {
        "source": f"To create a LSC project, source connection info is needed in resource: {access_resource_path}",
        "credentials": f"To create a LSC project, connection credentials info is needed in resource: {access_resource_path}",
    }

    check_required_keys(governance, governance_required_keys)
    check_required_keys(access, access_required_keys)

    ###############################################################################
    # 3 Create initial Ro-Crate & build contextual entities
    ###############################################################################

    crate = ROCrate(gen_preview=True)
    project_uuid: Annotated[
        str,
        "Project UUID is a unique auto-generated identifier on creation of the project",
    ] = os.getenv("PROJECT_IDENTIFIER", str(uuid.uuid4()))

    #
    # Load project info and init RC 'Project' entity
    #

    governance["project"].setdefault("@id", f"proj-{project_uuid}")

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
            "identifier": project_props.identifier,
        },
    )

    crate.add(project_entity)

    #
    # Load requesting agent info and init RC 'Person' entity
    #

    requesting_agent_props = s.RequestingAgentProps(**governance["requesting_agent"])
    person_entity = m.Person(
        crate,
        identifier=f"requesting-agent-{project_uuid}",
        properties={
            "name": requesting_agent_props.name,
            "affiliation": {"@id": f"requesting-agent-org-{project_uuid}"},
        },
    )

    aff_entity = m.ContextEntity(
        crate,
        identifier=f"requesting-agent-org-{project_uuid}",
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
    update_resource_entity(
        project_resource_path, "project", project_props.dict(by_alias=True)
    )

    #
    # Load project repository info and init RC 'SoftwareSourceCode' entity
    #

    repo_props = s.SoftwareSourceCodeProps(**governance["repository"])

    repo_entity = m.ContextEntity(
        crate=crate,
        identifier=f"repo-{project_uuid}",
        properties={
            "@type": "SoftwareSourceCode",
            "name": repo_props.name,
            "description": repo_props.description,
            "codeRepository": f"{repo_props.codeRepository}proj-{project_uuid}",
        },
    )

    crate.add(repo_entity)
    crate.metadata["isBasedOn"] = {"@id": f"repo-{project_uuid}"}

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
    # 5 Build create action
    ###############################################################################

    # TODO: Add in CreateAction for this 'cr8tor' create function here

    ###############################################################################
    # 6 Finalise Crate metadata
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

    # Create a new bagit dir or open existing one
    # Write the crate into the data dir of the bag
    # Do not zip as the crate is version controlled
    if not dryrun:
        bag_dir = Path("./bagit")

        if bag_dir.exists() and bag_dir.is_dir():
            bag = bagit.Bag(str(bag_dir))

            # Update bag info from config.toml; This does not modify the External-Identifier.
            # Delete and recreate the bag if the External-Identifier needs to be changed.
            bag.info.update(**config["bagit-info"])
            log.info("Loaded existing bag")
        else:
            bag = init_bag(project_id=project_uuid, bag_dir=bag_dir, config=config)

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
