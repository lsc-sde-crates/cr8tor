"""Utility functions for use in other modules."""

import logging
import os
import uuid
from hashlib import md5
from pathlib import Path
from typing import Annotated

import bagit
import rich
from pydantic import HttpUrl
from rich.console import Console
from rich.logging import RichHandler
from rocrate.rocrate import ROCrate
import tomllib


console = Console()


logging.basicConfig(
    level=logging.DEBUG if os.getenv("DEBUG") else logging.INFO,
    format="%(message)s",
    datefmt="[%Y-%m-%d %H:%M:%S]",
    handlers=[RichHandler(rich_tracebacks=True, console=console, markup=True)],
)

log = logging.getLogger("rich")


def make_uuid(
    x: str | HttpUrl,
) -> Annotated[
    str, "Unique URN:UUID identifier derived from MD5 hash of given string."
]:
    """
    Generate a unique URN:UUID identifier derived from the MD5 hash of the given string.
    Args:
        x (str | HttpUrl): Input which can be a string or an HTTP URL.
    Returns:
        Annotated[str, "Unique URN:UUID identifier derived from MD5 hash of project id."]:
        A unique URN:UUID identifier derived from the MD5 hash of the project ID.
    """

    hx = md5(str(x).encode()).hexdigest()
    return uuid.UUID(hex=hx).urn


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


def get_config(f: Path) -> dict:
    """
    Reads a TOML configuration file and returns its contents as a dictionary.
    Args:
        f (Path): The path to the TOML file.
    Returns:
        dict: The contents of the TOML file as a dictionary.
    Raises:
        FileNotFoundError: If the file does not exist.
        IsADirectoryError: If the path is a directory.
        tomllib.TOMLDecodeError: If the file is not a valid TOML file.
        OSError: If there is an issue opening the file.
    """

    return tomllib.load(f.open("rb"))
