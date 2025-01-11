# CR8TOR Examples

## Simple Project

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
