from neutron.api import extensions
from neutron.api.v2 import attributes

EXTPORT = 'external_port'
EXTENDED_ATTRIBUTES_2_0 = {
    'ports': {
        EXTPORT: {'allow_post': True, 'allow_put': True,
                  'default': [],
                  'enforce_policy': True,
                  'is_visible': True},
    }
}


class Extport(extensions.ExtensionDescriptor):
    """Extension class supporting external port."""

    @classmethod
    def get_name(cls):
        return "External Port"

    @classmethod
    def get_alias(cls):
        return "extport"

    @classmethod
    def get_description(cls):
        return "Adds the external port functionality to the default port implementation."

    @classmethod
    def get_updated(cls):
        return "2012-07-23T10:00:00-00:00"

    def get_extended_resources(self, version):
        if version == "2.0":
            return EXTENDED_ATTRIBUTES_2_0
        else:
            return {}
