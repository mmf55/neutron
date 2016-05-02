import abc

from neutron.api import extensions
from neutron.api.v2 import base
from neutron import manager

RESOURCE_NAME = "extnodeint"
COLLECTION_NAME = "%ss" % RESOURCE_NAME

# Attribute Map for extinterface resource
RESOURCE_ATTRIBUTE_MAP = {
    COLLECTION_NAME: {
        'id': {'allow_post': False, 'allow_put': False,
               'validate': {'type:uuid': None},
               'is_visible': True},
        'name': {'allow_post': True, 'allow_put': False,
                 'validate': {'type:string': None},
                 'is_visible': True, 'default': 'no_name'},
        'type': {'allow_post': True, 'allow_put': False,
                 'required_by_policy': True,
                 'is_visible': True},
        'extnodename': {'allow_post': True, 'allow_put': False,
                        'validate': {'type:string': None},
                        'is_visible': True, 'default': 'no_name'},
        'tenant_id': {'allow_post': True, 'allow_put': False,
                      'required_by_policy': True,
                      'validate': {'type:uuid': None},
                      'is_visible': True}
    }
}


class ExtNodeIntPluginInterface(extensions.PluginInterface):
    @abc.abstractmethod
    def create_extnodeint(self, context, extnodeint):
        """Create a new ExtInterface.
        This entity represents an external interface on the Campus Network NaaS plugin."""
        pass

    @abc.abstractmethod
    def delete_extnodeint(self, context, id):
        """Delete a ExtInterface using the given ID."""
        pass

    @abc.abstractmethod
    def get_extnodeint(self, context, id, fields):
        """Return the info related to a ExtInterface represented by the given ID."""
        pass

    @abc.abstractmethod
    def get_extnodeint(self, context, filters, fields):
        """Returns a list with all registered ExtInterface."""
        pass

    @abc.abstractmethod
    def update_extnodeint(self, context, id, extnodeint):
        """Updates database with new information about the ExtInterface represented by the given ID."""
        pass


class Extnodeint(extensions.ExtensionDescriptor):
    def __init__(self):
        pass

    def get_plugin_interface(self):
        return ExtNodeIntPluginInterface

    def get_name(self):
        # You can coin a name for this extension
        return "External Node Interface Extension"

    def get_alias(self):
        # This alias will be used by your core_plugin class to load
        # the extension
        return "extnodeint"

    def get_description(self):
        # A small description about this extension
        return "This is the external node interface representation of the NaaS network implementation."

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
