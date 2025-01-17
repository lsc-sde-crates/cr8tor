from pathlib import Path
from typing import Annotated

import typer
from rocrate.rocrate import ROCrate

from cr8tor.cli.crateops import app as cli_crateops
from cr8tor.cli.display import print_bagit, print_crate
from cr8tor.cli.initiate import app as cli_initiate

app = typer.Typer()
app.add_typer(cli_crateops)
app.add_typer(cli_initiate)


@app.command(name="read")
def read_bag(bag_dir: Annotated[Path, typer.Option(default="-i")] = "./bagit"):
    """
    Reads a Research Object Crate (RO-Crate) from the specified directory and prints its details in a table format.
    """

    print_bagit(bag_dir)
    crate = ROCrate(bag_dir / "data")
    print_crate(crate)


if __name__ == "__main__":
    app()
