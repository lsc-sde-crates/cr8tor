import bagit
import typer
import rocrate.model as m
import cr8tor.core.schema as s
import cr8tor.core.resourceops as project_resources
from pathlib import Path
from typing import Annotated
from rocrate.rocrate import ROCrate

from cr8tor.exception import DirectoryNotFoundError
from cr8tor.utils import log, make_uuid
from cr8tor.cli.display import print_crate

app = typer.Typer()


def init_bag(project_id: str, bagit_dir: Path, config: dict) -> bagit.Bag:
    """
    Initializes a BagIt bag for a given project.
    Args:
        project_id (str): The unique identifier for the project.
        bagit_dir (Path): The directory where the bag will be created.
        config (dict): Configuration dictionary containing BagIt metadata.
    Returns:
        bagit.Bag: The created BagIt bag object.
    Raises:
        OSError: If the directory cannot be created.
        bagit.BagError: If there is an error creating the bag.
    """

    bagit_dir.mkdir(parents=True, exist_ok=True)

    bag: bagit.Bag = bagit.make_bag(bag_dir=bagit_dir, checksums=["sha512"])

    # bag.info.update(s.BagitInfo(**config["bagit-info"])) # ToDo: Fix serialisation alias issue
    bag.info.update(**config["bagit-info"])
    bag.info["External-Identifier"] = make_uuid(project_id)

    return bag


def check_required_keys(data: dict, required_keys: dict):
    for key, error_message in required_keys.items():
        if key not in data:
            raise KeyError(error_message)


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
    """
    Builds the RO-Crate data crate for the target Cr8tor project using the specified metadata resources and configuration.

    This command performs the following actions:
    - Reads the configuration from the specified TOML file.
    - Includes resources from the specified directory into the RO-Crate.
    - If the `dryrun` option is provided, prints the crate details without writing to the "crate/" directory.

    Args:
        resources_dir (Path): Directory containing resources to include in the RO-Crate. Defaults to "./resources".
        config_file (Path): Location of the configuration TOML file. Defaults to "./config.toml".
        dryrun (bool): If True, prints the crate details without writing to the "crate/" directory. Defaults to False.

    Example usage:
        cr8tor build -i path-to-resources-dir -c path-to-config-file --dryrun
    """
    ###############################################################################
    # 1 Validate project build materials (i.e. resources/ & config.toml)
    ###############################################################################

    config = project_resources.read_resource(config_file)

    if not resources_dir.exists():
        raise DirectoryNotFoundError(resources_dir)

    project_resource_path = resources_dir.joinpath("governance", "project.toml")
    governance = project_resources.read_resource(project_resource_path)

    access_resource_path = resources_dir.joinpath("access", "access.toml")
    access = project_resources.read_resource(access_resource_path)

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
    requesting_agent_props = s.AgentProps(**governance["requesting_agent"])
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

    # contract_props = s.DataAccessContract(
    #     source=s.DatabricksSourceConnection(**access["source"]),
    #     credentials=s.SourceAccessCredential(**access["credentials"]),
    #     project_name=governance["project"]["project_name"],
    #     project_start_time=governance["project"]["project_start_time"],
    #     destination_type=governance["project"]["destination_type"],
    #     destination_format=governance["project"]["destination_format"],
    #     metadata=None
    # )
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
    # Metadata resources
    #

    for f in resources_dir.joinpath("metadata").glob("dataset*.toml"):
        dataset_dict = project_resources.read_resource(f)
        dataset_props = s.DatasetMetadata(**dataset_dict)

        crate.add_file(
            source=f,
            dest_path=f"metadata/{f.name}",
            properties={
                "name": dataset_props.name,
                "description": dataset_props.description,
            },
        )

        hasparts = []

        if dataset_props.staging_path is not None:
            staging_entity = m.ContextEntity(
                crate=crate,
                identifier=f"{dataset_props.name}-staging",
                properties={
                    "@type": "Dataset",
                    "name": f"{dataset_props.name} (Staging)",
                    "url": f"{dataset_props.staging_path}",
                    "encodingFormat": "application/x-duckdb",  # TODO: add format from project metadata
                },
            )
            crate.add(staging_entity)
            hasparts.append({"@id": staging_entity.id})

        if dataset_props.publish_path is not None:
            publish_entity = m.ContextEntity(
                crate=crate,
                identifier=f"{dataset_props.name}-publish",
                properties={
                    "@type": "Dataset",
                    "name": f"{dataset_props.name} (Publish)",
                    "url": f"{dataset_props.publish_path}",
                    "encodingFormat": "application/x-duckdb",  # TODO: add format from project metadata
                },
            )
            crate.add(publish_entity)
            hasparts.append({"@id": publish_entity.id})

        data_ctx_entity = m.ContextEntity(
            crate=crate,
            identifier=f"{dataset_props.name}",
            properties={
                "@type": "Dataset",
                "name": f"{dataset_props.name}",
                "description": dataset_props.description,
                "hasPart": hasparts,
            },
        )

        crate.add(data_ctx_entity)

    #
    # Access resources
    #

    access_source = s.DatabricksSourceConnection(**access["source"])
    crate.add_file(
        source=access_resource_path,
        dest_path="access/access.toml",
        properties={"name": access_source.name},
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
            result=[item.model_dump() for item in action_props.result],
            properties={
                "@type": action_props.type,
                "name": action_props.name,
                "startTime": action_props.start_time.isoformat(),
                "endTime": action_props.end_time.isoformat(),
                "actionStatus": action_props.action_status,
                "agent": action_props.agent,
            },
        )

    ###############################################################################
    # 7 Add Ro-crate meta to bagit directory structure
    ###############################################################################
    if not dryrun:
        bagit_dir = Path("./bagit")

        if bagit_dir.exists() and bagit_dir.is_dir():
            bag = bagit.Bag(str(bagit_dir))

            # Update bag info from config.toml; This does not modify the External-Identifier.
            # Delete and recreate the bag if the External-Identifier needs to be changed.
            bag.info.update(**config["bagit-info"])
            log.info("Loaded existing bag")
        else:
            bag = init_bag(
                project_id=project_props.id, bagit_dir=bagit_dir, config=config
            )

        crate.write(bagit_dir / "data")
        bag.save(manifests=True)

        n_payload_files = len(list(bag.payload_files()))
        log.info(
            f"[cyan]RO-Crate BagIt created at[/cyan] - [bold magenta]{bagit_dir} with {n_payload_files} files.[/bold magenta]",
        )
    else:
        log.warning(
            "[bold red]Dry run option set. Crate will not be written to disk.[/bold red]\n"
        )

    print_crate(crate=crate)
