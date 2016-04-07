import abc

from neutron.api import extensions
from neutron.api.v2 import base
from neutron import manager

RESOURCE_NAME = "extinterface"
COLLECTION_NAME = "%ss" % RESOURCE_NAME

# Attribute Map for extinterface resource
RESOURCE_ATTRIBUTE_MAP = {
    COLLECTION_NAME: {
        'id': {'allow_post': False, 'allow_put': False,
               'validate': {'type:uuid': None},
               'is_visible': True},
        'extnode_id': {'allow_post': True, 'allow_put': False,
                       'validate': {'type:string': None},
                       'required_by_policy': True,
                       'is_visible': True, 'default': ''},
        'extnode_name': {'allow_post': True, 'allow_put': False,
                         'required_by_policy': False,
                         'is_visible': True},
        'type': {'allow_post': True, 'allow_put': False,
                 'validate': {'type:string': None},
                 'required_by_policy': True,
                 'is_visible': True},
        'tenant_id': {'allow_post': False, 'allow_put': False,
                      'validate': {'type:uuid': None},
                      'required_by_policy': True,
                      'is_visible': True},
        'network_id': {'allow_post': True, 'allow_put': False,
                       'validate': {'type:string': None},
                       'required_by_policy': True,
                       'is_visible': True},
    }
}


class ExtInterfacePluginInterface(extensions.PluginInterface):
    @abc.abstractmethod
    def create_extinterface(self, context, ext_interface):
        """Create a new ExtInterface.
        This entity represents an external interface on the Campus Network NaaS plugin."""
        pass

    @abc.abstractmethod
    def delete_extinterface(self, context, id):
        """Delete a ExtInterface using the given ID."""
        pass

    @abc.abstractmethod
    def show_extinterface(self, context, id):
        """Return the info related to a ExtInterface represented by the given ID."""
        pass

    @abc.abstractmethod
    def list_extinterface(self, context):
        """Returns a list with all registered ExtInterface."""
        pass

    @abc.abstractmethod
    def update_extinterface(self, context, ext_interface):
        """Updates database with new information about the ExtInterface represented by the given ID."""
        pass


class ExtInterface(extensions.ExtensionDescriptor):
    def __init__(self):
        pass

    def get_plugin_interface(self):
        return ExtInterfacePluginInterface

    def get_name(self):
        # You can coin a name for this extension
        return "External Interface Extension"

    def get_alias(self):
        # This alias will be used by your core_plugin class to load
        # the extension
        return "extinterface"

    def get_description(self):
        # A small description about this extension
        return "This is the external interface representation of the NaaS network implementation."

    def get_updated(self):
        # Specify when was this extension last updated,
        # good for management when there are changes in the design
        return "2016-02-29T10:00:00-00:00"

    def get_resources(self):
        exts = []
        plugin = manager.NeutronManager.get_plugin()
        params = RESOURCE_ATTRIBUTE_MAP.get(COLLECTION_NAME, {})
        controller = base.create_resource(COLLECTION_NAME,
                                          RESOURCE_NAME,
                                          plugin,
                                          params,
                                          allow_bulk=False)
        extension = extensions.RequestExtension(COLLECTION_NAME, controller)
        exts.append(extension)
        return exts

    def get_extended_resources(self, version):
        if version == "2.0":
            return RESOURCE_ATTRIBUTE_MAP
        return {}
