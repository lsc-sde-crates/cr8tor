# Example usage

1. Follow the instructions in the **Development** to install `cr8tor`.
2. If using the `.venv` in the `cr8tor` development directory, make sure the environment has been activated.
3. Open a terminal and `cd` into the `cr8tor-examples` directory (parralel to cr8tor directory. mkdir the folder if does not exists). VSCode workspace should recognize it by default.
4. Review the files in the resources directory. These will be used to build the RO-Crate. See [Update DAR files](./../user-guide/update-resources-files.md) for details on updating the files in the resources directory.
5. Run `cr8tor initiate -t '..\cr8-cookiecutter\'` to initiate a new project. Answer the prompts.
6. `cd` into the project folder.
7. Run `cr8tor create -i ./resources -a "AgentName" --dryrun` to check everything works and review the entities that will be created in the RO-Crate. The crate will be created in a new directory called `bagit` alongside the `resources` directory. Replace AgentName with the correct value.
8. Now run `cr8tor create -i ./resources -a "AgentName"` to build the bagit crate. Replace AgentName with the correct value.
9. Open `bagit/data/ro-crate-preview.html` in a browser to preview the bagit crate and its contents.
10. Run `cr8tor read -i ./bagit`. If this succeeds, then the contents of the `bagit` folder form a valid RO-Crate.
