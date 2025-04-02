# Development

1. Clone the repository
2. Install [uv](https://docs.astral.sh/uv/)
3. Run `uv sync` in the project root. This will create a `.venv` folder and install all the project dependencies.
4. Activate the virtual environment with as below:
   1. Windows: `./.venv/Scripts/activate`
   2. MacOs/Linux: `source .venv/bin/activate`
5. Run `uv pip install -e .[dev]` to install `cr8tor` in _editable_ mode.
6. Run `pre-commit install` to enable pre-commit hooks.
