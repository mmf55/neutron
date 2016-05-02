import abc

from neutron.api import extensions
from neutron.api.v2 import base
from neutron.api.v2 import attributes
from neutron import manager

from neutron.plugins.ml2.common import extnet_validators

# You have to specify the attributes neutron-server should expect when
# someone invokes this plugin. Let's say you want
# 'name', 'priority', 'credential' for your extension /foxinsocks
# then following dictionary must be declared.
# I am following the naming convention used by other extensions.

RESOURCE_NAME = "extconnection"
COLLECTION_NAME = "%ss" % RESOURCE_NAME
# Collection name is the path identifier of the extension in the URI!

# Attribute Map for extnode resource
RESOURCE_ATTRIBUTE_MAP = {
    COLLECTION_NAME: {
        'id': {'allow_post': False, 'allow_put': False,
               'validate': {'type:uuid': None},
               'is_visible': True
               },
        'types_supported': {'allow_post': True, 'allow_put': True,
                            'required_by_policy': True,
                            'validate': {'type:extnet_overlay_types': None},
                            'is_visible': True},
        'ids_pool': {'allow_post': True, 'allow_put': True,
                     'required_by_policy': False,
                     'validate': {'type:extnet_ids_pool': None},
                     'is_visible': True},
        'extnodeint1': {'allow_post': True, 'allow_put': True,
                        'required_by_policy': False,
                        'default': None,
                        'is_visible': True},
        'extnodeint2': {'allow_post': True, 'allow_put': True,
                        'required_by_policy': False,
                        'default': None,
                        'is_visible': True},
    }
}

validator_func_types = extnet_validators.validate_types_supported
validator_func_ids_pool = extnet_validators.validate_ids_pool
attributes.validators['type:extnet_overlay_types'] = validator_func_types
attributes.validators['type:extnet_ids_pool'] = validator_func_ids_pool


class ExtConnectionPluginInterface(extensions.PluginInterface):
    @abc.abstractmethod
    def create_extconnection(self, context, extconnection):
        """Create a new ExtNode. This entity represents a physical network device on the Campus Network NaaS plugin."""
        pass

    @abc.abstractmethod
    def delete_extconnection(self, context, id):
        """Delete a ExtNode using the given ID."""
        pass

    @abc.abstractmethod
    def get_extconnection(self, context, id, fields):
        """Return the info related to a ExtNode represented by the given ID."""
        pass

    @abc.abstractmethod
    def get_extconnection(self, context, filters, fields):
        """Returns a list with all registered ExtNodes."""
        pass

    @abc.abstractmethod
    def update_extconnection(self, context, id, extconnection):
        """Updates database with new information about the ExtNode represented by the given ID."""
        pass


class Extconnection(extensions.ExtensionDescriptor):
    def __init__(self):
        pass

    def get_plugin_interface(self):
        return ExtConnectionPluginInterface

    def get_name(self):
        # You can coin a name for this extension
        return "External Connection Extension"

    def get_alias(self):
        # This alias will be used by your core_plugin class to load
        # the extension
        return "extconnection"

    def get_description(self):
        # A small description about this extension
        return "This is the physical connection representation of the NaaS network implementation."

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
