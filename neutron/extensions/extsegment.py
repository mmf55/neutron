import abc

from neutron.api import extensions
from neutron.api.v2 import base
from neutron import manager

RESOURCE_NAME = "extsegment"
COLLECTION_NAME = "%ss" % RESOURCE_NAME

# Attribute Map for extsegment resource
RESOURCE_ATTRIBUTE_MAP = {
    COLLECTION_NAME: {
        'id': {'allow_post': False, 'allow_put': False,
               'validate': {'type:uuid': None},
               'is_visible': True
               },
        'name': {'allow_post': True, 'allow_put': False,
                 'validate': {'type:string': None},
                 'is_visible': True, 'default': ''},
        'types_supported': {'allow_post': True, 'allow_put': False,
                            'required_by_policy': True,
                            'validate': {'type:string': None},
                            'is_visible': True, 'default': ''},
        'id_pool': {'allow_post': True, 'allow_put': False,
                    'required_by_policy': False,
                    'is_visible': True}
    }
}


class ExtSegmentPluginInterface(extensions.PluginInterface):
    @abc.abstractmethod
    def create_extsegment(self, context, ext_segment):
        """Create a new ExtSegment.
        This entity represents a physical network segment on the Campus Network NaaS plugin."""
        pass

    @abc.abstractmethod
    def delete_extsegment(self, context, id):
        """Delete a ExtSegment using the given ID."""
        pass

    @abc.abstractmethod
    def show_extsegment(self, context, id):
        """Return the info related to a ExtSegment represented by the given ID."""
        pass

    @abc.abstractmethod
    def list_extsegment(self, context):
        """Returns a list with all registered ExtSegment."""
        pass

    @abc.abstractmethod
    def update_extsegment(self, context, ext_segment):
        """Updates database with new information about the ExtSegment represented by the given ID."""
        pass


class Extsegment(extensions.ExtensionDescriptor):
    def __init__(self):
        pass

    def get_plugin_interface(self):
        return ExtSegmentPluginInterface

    def get_name(self):
        # You can coin a name for this extension
        return "External segment Extension"

    def get_alias(self):
        # This alias will be used by your core_plugin class to load
        # the extension
        return "extsegment"

    def get_description(self):
        # A small description about this extension
        return "This is the segment representation of the NaaS network implementation."

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
