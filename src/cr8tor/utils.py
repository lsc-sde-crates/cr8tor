"""Utility functions for use in other modules."""

import logging
import os
import uuid
from hashlib import md5
from pathlib import Path
from typing import Annotated

import tomllib
from pydantic import HttpUrl
from rich.console import Console
from rich.logging import RichHandler

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
