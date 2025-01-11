from pathlib import Path
from typing import Annotated

import rich
import rocrate.model as m
import typer
import yaml
from rocrate.rocrate import ROCrate

import cr8tor.schema as s

app = typer.Typer()


def print_crate(crate: ROCrate) -> None:
    table = rich.table.Table("Field", "Value", title="LSC SDE RO-Crate")
    table.add_row("Name", crate.name)
    table.add_row("Published", crate.datePublished.isoformat())
    table.add_row("Publisher", crate.publisher)
    table.add_row("License", crate.license)

    table.add_section()
    table.add_row("Entities", "", end_section=True)

    for e in crate.get_entities():
        table.add_row(e.type, e.id)

    rich.print(table)


@app.command(name="create")
def create(
    resources_dir: Annotated[str, typer.Option(default="-i")] = "./resources",
    dryrun: Annotated[bool, typer.Option(default="--dryrun")] = False,
):
    """
    Create a Research Object Crate (RO-Crate) from the specified resources directory.
    This function generates an RO-Crate by loading project and dataset metadata from YAML files
    located in the provided resources directory. The crate is populated with project information,
    governance details, and dataset metadata, and then written to the "crate/" directory.

    If the `dryrun` argument is provided, the function will print the crate details without writing to the "crate/" directory.

    Example:
        $ cr8tor create -i /path/to/resources
    """

    resources_dir: Path = Path(resources_dir)
    crate = ROCrate(gen_preview=True)

    # Load project information

    with resources_dir.joinpath("governance", "project.yaml").open() as f:
        governance = yaml.safe_load(f)

    project = s.Project(**governance["project"])

    ro_project = m.ContextEntity(
        crate=crate,
        identifier=project.identifier,
        properties={
            "@type": "Project",
            "@id": project.identifier,
        }.update(**project.model_dump()),
    )
    crate.add(ro_project)
    # Add governance yaml file to crate

    crate.add_file(
        source=resources_dir.joinpath("governance", "project.yaml"),
        dest_path="governance/project.yaml",
        properties={"name": project.name, "description": project.description},
    )

    # Validate and add dataset yaml files to crate

    for f in resources_dir.joinpath("metadata").glob("dataset*.yaml"):
        dataset = s.DatasetMetadata.model_validate(yaml.safe_load(f.open()))

        crate.add_file(
            source=f,
            dest_path=f"metadata/{f.name}",
            properties={"name": dataset.name, "description": dataset.description},
        )

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
    crate.mainEntity = ro_project

    # Finally write the crate (do not zip as the crate is version controlled)
    if not dryrun:
        crate.write("crate/")
    else:
        rich.print(
            "\n[bold red]Dry run option set. Crate will not be written to disk.[/bold red]\n"
        )

        print_crate(crate=crate)


@app.command(name="read")
def read_crate(crate_dir: Annotated[str, typer.Option(default="-i")] = "./crate"):
    """
    Reads a Research Object Crate (RO-Crate) from the specified directory and prints its details in a table format.
    """
    crate = ROCrate(crate_dir)
    print_crate(crate)


if __name__ == "__main__":
    app()
