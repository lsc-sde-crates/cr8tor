# Development

1. Clone the repository
2. Install [uv](https://docs.astral.sh/uv/)
3. Run `uv sync` in the project root. This will create a `.venv` folder and install all the project dependencies.
4. Activate the virtual environment with as below:
   1. Windows: `./.venv/Scripts/activate`
   2. MacOs/Linux: `source .venv/bin/activate`
5. Run `uv pip install -e .[dev]` to install `cr8tor` in _editable_ mode.
6. Run `pre-commit install` to enable pre-commit hooks.

## Usage

A minimal example is provided in `examples/simple_project`.

Run `cr8tor --help` for more information

1. Create a new project running:
   1. `uv run cr8tor initiate -t ./../cr8-cookiecutter/ -n "newproject" -org "lsc-sde-crates"` to omit cookiecutter prompts and use default values
   2. `uv run cr8tor initiate -t ./../cr8-cookiecutter/` to invoke cookiecutter prompts
2. Run `uv run cr8tor create -a GithubAction -i ./resources` to create a bagit package
3. Run `uv run cr8tor validate -a GithubAction -i ./resources` to create a bagit package
4. Run `uv run cr8tor sign-off -a GithubAction -agreement "url" -signing-entity "entity"` to add a sign-off activity
5. Run `uv run cr8tor stage-transfer -a GithubAction -i ./resources` to kick off data extraction
6. Run `uv run cr8tor disclosure -a GithubAction -agreement "url" -signing-entity "entity"` to add a disclosure activity
7. Run `uv run cr8tor publish -a GithubAction -i ./resources` to kick off data extraction

## Debugging in VSCode

1. Prepare launch.json with content

   ```json
   {
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Attach",
            "type": "debugpy",
            "request": "attach",
            "justMyCode": false,
            "connect": {
                "host": "127.0.0.1",
                "port": 5678,
            },
            "pathMappings": [
                {
                    "localRoot": "${workspaceFolder}",
                    "remoteRoot": "${workspaceFolder}"
                }
            ]
        }
    ]
   }
   ```

2. Run command you want to debug, e.g. `uv run python ./../src/cr8tor/main.py create`
3. Click F5 to invoke VSCode Debugger
