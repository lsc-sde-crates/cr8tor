"""Functions to work with RO-Crate objects"""

import os
import uuid
from pathlib import Path
from typing import Annotated

import bagit
import rocrate.model as m
import typer
import yaml
from rocrate.rocrate import ROCrate

import cr8tor.core.schema as s
from cr8tor.exception import DirectoryNotFoundError
from cr8tor.utils import get_config, log, make_uuid
from cr8tor.cli.display import print_crate

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

    config = get_config(config_file)

    # Raise exception if resources directory is not found.
    if not resources_dir.exists():
        raise DirectoryNotFoundError(resources_dir)

    crate = ROCrate(gen_preview=True)

    # TODO: Define CreateAction
    # crate.add_action()

    governance = yaml.safe_load(
        resources_dir.joinpath("governance", "project.yaml").read_text()
    )

    #
    # Project Conext Entity
    #
    project = s.ProjectProps(**governance["project"])
    project_uuid = str(uuid.uuid4())
    project_uuid: Annotated[
        str,
        "Unique Project Identifier should be the GitHub URL of the Project Crate Repo",
    ] = os.getenv("PROJECT_IDENTIFIER", project_uuid)

    log.info(
        f"[cyan]Creating RO-Crate for[/cyan] - [bold magenta]{project.name}[/bold magenta]",
    )

    projectEntity = m.ContextEntity(
        crate=crate,
        identifier="proj-" + project_uuid,
        properties={
            "@type": "Project",
            "name": project.name,
            "identifier": project.identifier,
            "memberOf": [{"@id": f"requester-{project_uuid}"}],
        },
    )
    crate.add(projectEntity)

    requester = s.RequestingAgentProps(**governance["requester"])
    #
    # Requester Affiliation Context Entity
    #
    affEntity = m.ContextEntity(
        crate,
        identifier=f"requester-org-{project_uuid}",
        properties={
            "@type": "Organisation",
            "name": requester.affiliation.name,
            "url": requester.affiliation.url,
        },
    )
    crate.add(affEntity)

    #
    # Requester Context Entity
    #

    requesterEntity = m.Person(
        crate,
        f"requester-{project_uuid}",
        properties={
            "name": requester.name,
            "affiliation": {"@id": f"requester-org-{project_uuid}"},
        },
    )
    crate.add(requesterEntity)

    #
    # Repository Conext Entity
    #
    repo = s.CodeRepositoryProps(**governance["repository"])

    repoEntity = m.ContextEntity(
        crate=crate,
        identifier=f"repo-{project_uuid}",
        properties={
            "@type": "SoftwareSourceCode",
            "name": repo.name,
            "description": repo.description,
            "codeRepository": f"{repo.url}proj-{project_uuid}",
        },
    )
    crate.add(repoEntity)
    crate.metadata["isBasedOn"] = {"@id": f"repo-{project_uuid}"}

    # Add governance yaml file to crate

    crate.add_file(
        source=resources_dir.joinpath("governance", "project.yaml"),
        dest_path="governance/project.yaml",
        properties={"name": project.name, "description": project.description},
    )

    log.info(
        msg="[cyan]Validated and added file[/cyan] - [bold magenta]governance/project.yaml[/bold magenta]",
    )

    # Validate and add dataset yaml files to crate

    for f in resources_dir.joinpath("metadata").glob("dataset*.yaml"):
        dataset = s.DatasetMetadata.model_validate(yaml.safe_load(f.open()))

        crate.add_file(
            source=f,
            dest_path=f"metadata/{f.name}",
            properties={"name": dataset.name, "description": dataset.description},
        )

        log.info(
            msg=f"[cyan]Validated and added file[/cyan] - [bold magenta]metadata/{f.name}[/bold magenta]",
        )

    # ToDo: Add any other yaml files with validation here

    # ToDo: Should we also add arbitrary other files in here as well - eg. markdown

    # Add root level metadata to the crate
    crate.name = project.name
    crate.description = project.description
    crate.license = s.CrateMeta.License
    crate.publisher = m.ContextEntity(
        crate,
        identifier=s.CrateMeta.Publisher,
        properties={
            "@type": "Organisation",
            "name": "LSC SDE",
            "url": "https://github.com/lsc-sde-crates",
        },
    )
    crate.mainEntity = projectEntity

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
