"""Module with functions to initiate a CR8 project"""

from datetime import datetime
from typing import Annotated, Optional

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
    checkout: Annotated[Optional[str], typer.Option()] = None,
    project_name: Annotated[Optional[str], typer.Option()] = None,
):
    """
    Initialize a new CR8 project using a specified cookiecutter template.
    Args:
        template_path (str): The GitHub URL or relative path to the cr8-cookiecutter template.
                             This is prompted from the user if not provided.
        project_name (Optional[str]): The name of the project to be created.
                                      This is optional and can be provided as an argument.
    The function generates a new project by applying the specified cookiecutter template.
    It also adds a timestamp to the context used by the template.
    The `template_path` argument is annotated with `typer.Option` to provide command-line
    interface options such as default value, help message, and prompt.
    Example:

        `cr8tor init -t https://github.com/lsc-sde-crates/cr8-cookiecutter`)

        or

        `cr8tor init -t path-to-local-cr8-cookiecutter-dir`

        or

        `cr8tor init -t path-to-local-cr8-cookiecutter-dir` --project-name "my-project"
    """

    extra_context = {
        "__timestamp": datetime.now().isoformat(timespec="seconds"),
        "__cr8_cc_template": template_path,
    }

    if project_name is not None:
        extra_context.update({"project_name": project_name})
        cookiecutter(
            template_path, checkout=checkout, extra_context=extra_context, no_input=True
        )
    else:
        cookiecutter(template_path, checkout=checkout, extra_context=extra_context)
