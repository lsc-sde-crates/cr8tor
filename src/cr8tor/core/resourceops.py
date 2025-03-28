"""Module to create, read, update and delete entities in resources.
This is different from crateops which is primarily concerned with taking the resources created/updated
by this module and packaging them into RO-Crate and BagIt archives.
"""

import toml
from cr8tor.utils import log
from pathlib import Path
#
# Whole file resource operations
#


def create_resource(resource_file_path: Path, data: dict):
    resource_file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(resource_file_path, "w") as f:
        toml.dump(data, f)


def read_resource(resource_file_path: Path) -> dict:
    try:
        return toml.load(resource_file_path)
    except FileNotFoundError:
        log.info(
            f"[red]Resource file missing[/red] - [bold red]{resource_file_path}[/bold red]",
        )
        return {"Error": f"The resource file '{resource_file_path}' is missing."}


def update_resource(resource_file_path, data: dict):
    if resource_file_path.exists():
        with open(resource_file_path, "w") as f:
            toml.dump(data, f)


def delete_resource(resource_file_path):
    pass


#
# Partial file resource operations
#


def create_resource_entity(resource_file_path: Path, property_key: str, new_object):
    resource_dict = toml.load(resource_file_path)
    resource_dict[property_key] = new_object

    with resource_file_path.open("w") as resource:
        toml.dump(resource_dict, resource)

    log.info(
        f"[cyan]Added entity {property_key} to resources file:[/cyan] - [bold magenta]{resource_file_path}[/bold magenta]",
    )


def read_resource_entity(resource_file_path: Path, property_key: str):
    try:
        return toml.load(resource_file_path)[property_key]
    except FileNotFoundError:
        log.info(
            f"[red]Entity missing in resource file[/red] - [bold red]{resource_file_path}[/bold red]",
        )
    return {
        "Error": f"The resource file '{resource_file_path}' is missing entity {property_key}."
    }


def update_resource_entity(resource_file_path: Path, property_key: str, object):
    resource_dict = toml.load(resource_file_path)

    if property_key not in resource_dict:
        raise KeyError(
            f"The property key for entity '{property_key}' does not exist in resource: {resource_file_path}"
        )

    target_entity = resource_dict.get(property_key)
    if isinstance(target_entity, dict):
        resource_dict[property_key].update(object)
    elif isinstance(target_entity, list):
        resource_dict[property_key].append(object)
    else:
        raise TypeError(
            f"Unexpected type when updating '{property_key}' in resource: {resource_file_path}"
        )

    with resource_file_path.open("w") as resource:
        toml.dump(resource_dict, resource)

    log.info(
        f"[cyan]Updated resources file:[/cyan] - [bold magenta]{resource_file_path}[/bold magenta]",
    )


def delete_resource_entity(
    resource_file_path: Path, property_key: str, attribute: str, value
):
    """
    Deletes an object from a list in a TOML file based on a given attribute.

    :param resource_file_path: Path to the TOML file
    :param property_key: Key in the TOML file that contains the list of objects
    :param attribute: The attribute to match for deletion
    :param value: The value of the attribute to match
    """
    resource_dict = toml.load(resource_file_path)

    if property_key not in resource_dict:
        raise KeyError(
            f"The property key for entity '{property_key}' does not exist in resource: {resource_file_path}"
        )

    target_entity = resource_dict.get(property_key)

    if isinstance(target_entity, list):
        original_length = len(target_entity)

        resource_dict[property_key] = [
            obj
            for obj in target_entity
            if not (isinstance(obj, dict) and obj.get(attribute) == value)
        ]

        if len(resource_dict[property_key]) == original_length:
            log.warning(
                f"No matching object found with {attribute} = {value} in '{property_key}'."
            )

    else:
        raise TypeError(
            f"Expected a list for '{property_key}', but found {type(target_entity).__name__} in resource: {resource_file_path}"
        )

    with resource_file_path.open("w") as resource:
        toml.dump(resource_dict, resource)

    log.info(
        f"[cyan]Deleted object from resources file:[/cyan] - [bold magenta]{resource_file_path}[/bold magenta]",
    )
