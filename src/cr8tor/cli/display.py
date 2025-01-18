"""Module for rich display to console."""

from pathlib import Path

import bagit
import rich
from rocrate.rocrate import ROCrate

from cr8tor.utils import console


def print_bagit(bag_dir: Path) -> None:
    """
    Print the metadata and contents of a BagIt archive in a formatted table.
    Args:
        bag_dir (Path): The directory path of the BagIt archive.
    Returns:
        None
    """
    bag = bagit.Bag(str(bag_dir))

    table = rich.table.Table()
    table.add_column("Field", justify="right", style="cyan", no_wrap=True)
    table.add_column("Value", style="magenta")

    for k, v in bag.info.items():
        table.add_row(k, v)

    table.add_section()
    table.add_row("Contents")
    table.add_section()

    for k, v in bag.payload_entries().items():
        table.add_row(k, str(v))

    panel = rich.panel.Panel(table, title="BagIt Archive Info")

    console.print(panel)


def print_crate(crate: ROCrate) -> None:
    """
    Prints the details of an RO-Crate in a formatted table.
    Args:
        crate (ROCrate): The RO-Crate object containing metadata and entities to be printed.
    Returns:
        None
    """

    table = rich.table.Table()
    table.add_column("Field", justify="right", style="cyan", no_wrap=True)
    table.add_column("Value", style="magenta")
    table.add_row("Name", crate.name)
    table.add_row("Published", crate.datePublished.isoformat())
    table.add_row("Publisher", crate.publisher)
    table.add_row("License", crate.license)

    table.add_section()
    table.add_row("Entities", "", end_section=True)

    for e in crate.get_entities():
        table.add_row(e.type, e.id)

    panel = rich.panel.Panel(
        renderable=table,
        title=f"RO-Crate - [bold cyan]{crate.name}[/bold cyan]",
    )

    console.print(panel)
