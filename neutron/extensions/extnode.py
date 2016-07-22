import abc

from neutron.api import extensions
from neutron.api.v2 import base
from neutron import manager

RESOURCE_NAME = "extnode"
COLLECTION_NAME = "%ss" % RESOURCE_NAME

# Attribute Map for extnode resource
RESOURCE_ATTRIBUTE_MAP = {
    COLLECTION_NAME: {
        'id': {'allow_post': False, 'allow_put': False,
               'validate': {'type:uuid': None},
               'is_visible': True},
        'name': {'allow_post': True, 'allow_put': True,
                 'required_by_policy': False,
                 'validate': {'type:string': None},
                 'is_visible': True, 'default': 'no_name'},
        'ip_address': {'allow_post': True, 'allow_put': True,
                       'required_by_policy': False,
                       'validate': {'type:ip_address_or_none': None},
                       'is_visible': True, 'default': None},
        'topology_discover': {'allow_post': True, 'allow_put': False,
                              'required_by_policy': True,
                              'validate': {'type:boolean': None},
                              'is_visible': True, 'default': False},
        'topology_discover_info': {'allow_post': False, 'allow_put': False,
                                   'validate': {'type:string': None},
                                   'is_visible': True, 'default': 'Not requested.'},

        'tenant_id': {'allow_post': True, 'allow_put': False,
                      'required_by_policy': True,
                      'validate': {'type:uuid': None},
                      'is_visible': True}
    }
}


class ExtNodePluginInterface(extensions.PluginInterface):
    @abc.abstractmethod
    def create_extnode(self, context, extnode):
        """Create a new ExtNode.
        This entity represents an external node on the Campus Network NaaS plugin."""
        pass

    @abc.abstractmethod
    def delete_extnode(self, context, id):
        """Delete a ExtNode using the given ID."""
        pass

    @abc.abstractmethod
    def get_extnode(self, context, id, fields):
        """Return the info related to a ExtNode represented by the given ID."""
        pass

    @abc.abstractmethod
    def get_extnode(self, context, filters, fields):
        """Returns a list with all registered ExtNode."""
        pass

    @abc.abstractmethod
    def update_extnode(self, context, id, extnode):
        """Updates database with new information about the ExtNode represented by the given ID."""
        pass


class Extnode(extensions.ExtensionDescriptor):
    def __init__(self):
        pass

    def get_plugin_node(self):
        return ExtNodePluginInterface

    def get_name(self):
        # You can coin a name for this extension
        return "External Node Extension"

    def get_alias(self):
        # This alias will be used by your core_plugin class to load
        # the extension
        return "extnode"

    def get_description(self):
        # A small description about this extension
        return "This is the external node representation of the NaaS network implementation."

    def get_updated(self):
        # Specify when was this extension last updated,
        # good for management when there are changes in the design
        return "2016-02-29T10:00:00-00:00"

    def get_resources(self):
        exts = list()
        plugin = manager.NeutronManager.get_plugin()
        params = RESOURCE_ATTRIBUTE_MAP.get(COLLECTION_NAME, dict())
        controller = base.create_resource(COLLECTION_NAME,
                                          RESOURCE_NAME,
                                          plugin,
                                          params,
                                          allow_bulk=False)
        extension = extensions.ResourceExtension(COLLECTION_NAME, controller)
        exts.append(extension)
        return exts

    def get_extended_resources(self, version):
        if version == "2.0":
            return RESOURCE_ATTRIBUTE_MAP
        return {}
