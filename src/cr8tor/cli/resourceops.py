"""Module to create, read, update and delete entities in resources.
This is different from crateops which is primarily concerned with taking the resources created/updated
by this module and packaging them into RO-Crate and BagIt archives.
"""

import yaml
from cr8tor.utils import log

#
# Whole file resource operations
#


def create_resource(resource_file_path):
    pass


def read_resource(resource_file_path):
    try:
        return yaml.safe_load(resource_file_path.read_text())
    except FileNotFoundError:
        log.info(
            f"[red]Resource file missing[/red] - [bold red]{resource_file_path}[/bold red]",
        )
        return {"Error": f"The resource file '{resource_file_path}' is missing."}


def update_resource(resource_file_path):
    pass


def delete_resource(resource_file_path):
    pass


#
# Partial file resource operations
#


def create_resource_entity(resource_file_path, property_key, modified_object):
    pass


def read_resource_entity(resource_file_path, property_key):
    pass


def update_resource_entity(resource_file_path, property_key, modified_object):
    resource_dict = yaml.safe_load(resource_file_path.read_text())

    if property_key not in resource_dict:
        raise KeyError(
            f"The property key for entity '{property_key}' does not exist in resource: {resource_file_path}"
        )

    resource_dict[property_key].update(modified_object)
    dict_obj_str = yaml.dump(resource_dict, default_flow_style=False)

    resource_file_path.write_text(dict_obj_str)

    log.info(
        f"[cyan]Updated resources file:[/cyan] - [bold magenta]{resource_file_path}[/bold magenta]",
    )


def delete_resource_entity(resource_file_path, property_key):
    pass
