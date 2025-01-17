"""Module with functions to initiate a CR8 project"""

from datetime import datetime
from typing import Annotated

import typer
from cookiecutter.main import cookiecutter

app = typer.Typer()


@app.command(name="init")
def init(
    template_path: Annotated[
        str,
        typer.Option(
            default="-t",
            help="Github URL or relative path to cr8-cookiecutter template",
            prompt=True,
        ),
    ],
):
    """
    Initialize a new CR8 project using a specified cookiecutter template.
    Args:
        template_path (str): The GitHub URL or relative path to the cr8-cookiecutter template.
                             This is prompted from the user if not provided.
    The function generates a new project by applying the specified cookiecutter template.
    It also adds a timestamp to the context used by the template.
    The `template_path` argument is annotated with `typer.Option` to provide command-line
    interface options such as default value, help message, and prompt.
    Example:

        `cr8tor init -t https://github.com/lsc-sde-crates/cr8-cookiecutter`)

        or

        `cr8tor init -t path-to-local-cr8-cookiecutter-dir`
    """

    extra_context = {
        "__timestamp": datetime.now().isoformat(timespec="seconds"),
        "__cr8_cc_template": template_path,
    }

    cookiecutter(template_path, extra_context=extra_context)
