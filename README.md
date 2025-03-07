# cr8tor

`cr8tor` is a command-line tool designed to help create, validate and update [5-Safes RO-Crates (5s-crates)](https://trefx.uk/5s-crate/) objects for use within the [Lancashire and South Cumbria Secure Data Environment (LSC SDE)](https://github.com/lsc-sde).

5s-crates are used to manage data ingress and egress out of LSC SDE's Kubernetes Research Analytics Platform.

## Development

(ToDo: Add more detail here)

1. Clone this repository
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

# CR8TOR Example

ToDo:

- Update this documentation.
- Create a cr8tor template project repository

1. Follow the instructions in the [README]('../README.md) file to install `cr8tor`.
2. If using the `.venv` in the `cr8tor` development directory, make sure the environment has been activated.
3. Open a terminal and `cd` into the `simple_project` directory.
4. Review the files in the resources directory. These will be used to build the RO-Crate
5. Run `cr8tor create -i ./resources --dryrun` to check everything works and review the entities that will be created in the RO-Crate. The crate will be created in a new directory called `crate` alongside the `resources` directory.
6. Now run `cr8tor create -i ./resources` to build the crate.
7. Open `crate/ro-crate-preview.html` in a browser to preview the crate and its contents.
8. Run `cr8tor read -i ./crate`. If this succeeds, then the contents of the `crate` folderform a valid RO-Crate.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
