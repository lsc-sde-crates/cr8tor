import debugpy
from pathlib import Path
from typing import Annotated
from dotenv import load_dotenv, find_dotenv
import typer
from rocrate.rocrate import ROCrate

# from cr8tor.cli.create import app as cli_commands
from cr8tor.cli import app as cli
from cr8tor.cli.display import print_bagit, print_crate
from cr8tor.cli.initiate import app as cli_initiate

app = typer.Typer()
app.add_typer(cli)
app.add_typer(cli_initiate)


@app.command(name="read")
def read_bag(bagit_dir: Annotated[Path, typer.Option(default="-i")] = "./bagit"):
    """
    Reads a Research Object Crate (RO-Crate) from the specified directory and prints its details in a table format.
    """

    print_bagit(bagit_dir)
    crate = ROCrate(bagit_dir / "data")
    print_crate(crate)


if __name__ == "__main__":
    debugpy.listen(("localhost", 5678))
    debugpy.wait_for_client()

    load_dotenv(find_dotenv())
    app()
