import typer
from cr8tor.cli.create import app as create_command
from cr8tor.cli.build import app as build_command
from cr8tor.cli.validate import app as validate_command
from cr8tor.cli.sign_off import app as sign_off_command
from cr8tor.cli.stage_transfer import app as stage_transfer_command
from cr8tor.cli.publish import app as publish_command

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

app = typer.Typer()
app.add_typer(create_command)
app.add_typer(build_command)
app.add_typer(validate_command)
app.add_typer(sign_off_command)
app.add_typer(stage_transfer_command)
app.add_typer(publish_command)
