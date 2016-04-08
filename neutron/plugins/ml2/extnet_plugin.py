from neutron.plugins.ml2 import plugin
from neutron.db import ext_network_db_mixin

from oslo_log import log as logging

LOG = logging.getLogger(__name__)


class ExtNetworkML2(plugin.Ml2Plugin,
                    ext_network_db_mixin.ExtNetworkDBMixin):
    # List of all the extensions supported by the plugin extension
    extensions_supported = ['extnode',
                            'extsegment',
                            'extlink',
                            'extinterface'
                            ]

    def __init__(self):
        for extension in self.extensions_supported:
            self._supported_extension_aliases.append(extension)
        super(ExtNetworkML2, self).__init__()

    def create_extnode(self, context, ext_node):
        LOG.debug("I got here!!!!")
        super(ExtNetworkML2, self).create_extnode(context, ext_node)

    def create_extsegment(self, context, ext_segment):
        super(ExtNetworkML2, self).create_extsegment(context, ext_segment)
