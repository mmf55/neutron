import abc

from neutron.api import extensions
from neutron.api.v2 import base
from neutron import manager

RESOURCE_NAME = "extlink"
COLLECTION_NAME = "%ss" % RESOURCE_NAME

# Attribute Map for extlink resource
RESOURCE_ATTRIBUTE_MAP = {
    COLLECTION_NAME: {
        'id': {'allow_post': False, 'allow_put': False,
               'validate': {'type:uuid': None},
               'is_visible': True
               },
        'type': {'allow_post': True, 'allow_put': False,
                 'required_by_policy': True,
                 'validate': {'type:string': None},
                 'is_visible': True, 'default': ''},
        'network_id': {'allow_post': True, 'allow_put': False,
                       'validate': {'type:string': None},
                       'required_by_policy': True,
                       'is_visible': True},
        'overlay_id': {'allow_post': True, 'allow_put': False,
                       'validate': {'type:string': None},
                       'is_visible': True},
        'segment_id': {'allow_post': True, 'allow_put': False,
                       'required_by_policy': True,
                       'validate': {'type:uuid': None},
                       'is_visible': True},
    }
}


class ExtLinkPluginInterface(extensions.PluginInterface):
    @abc.abstractmethod
    def create_extlink(self, context, ext_link):
        """Create a new ExtSegment.
        This entity represents a physical network segment on the Campus Network NaaS plugin."""
        pass

    @abc.abstractmethod
    def delete_extlink(self, context, id):
        """Delete a ExtSegment using the given ID."""
        pass

    @abc.abstractmethod
    def show_extlink(self, context, id):
        """Return the info related to a ExtSegment represented by the given ID."""
        pass

    @abc.abstractmethod
    def list_extlink(self, context):
        """Returns a list with all registered ExtSegment."""
        pass

    @abc.abstractmethod
    def update_extlink(self, context, ext_link):
        """Updates database with new information about the ExtSegment represented by the given ID."""
        pass


class Extlink(extensions.ExtensionDescriptor):
    def __init__(self):
        pass

    def get_plugin_interface(self):
        return ExtLinkPluginInterface

    def get_name(self):
        # You can coin a name for this extension
        return "External link Extension"

    def get_alias(self):
        # This alias will be used by your core_plugin class to load
        # the extension
        return "extlink"

    def get_description(self):
        # A small description about this extension
        return "This is the link representation of the NaaS network implementation."

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
