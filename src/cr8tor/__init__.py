import logging
import os

from rich.console import Console
from rich.logging import RichHandler

from cr8tor.schema import (
    ColumnMetadata,
    DatasetMetadata,
    Project,
    RequestingAgent,
    TableMetadata,
)

__all__ = [
    "Project",
    "RequestingAgent",
    "ColumnMetadata",
    "TableMetadata",
    "DatasetMetadata",
]

console = Console()


logging.basicConfig(
    level=logging.DEBUG if os.getenv("DEBUG") else logging.INFO,
    format="%(message)s",
    datefmt="[%Y-%m-%d %H:%M:%S]",
    handlers=[RichHandler(rich_tracebacks=True, console=console, markup=True)],
)

log = logging.getLogger("rich")
