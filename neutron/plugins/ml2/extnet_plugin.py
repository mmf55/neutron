from neutron.plugins.ml2 import plugin
from neutron.db import extnet_db_mixin

from oslo_log import log as logging

LOG = logging.getLogger(__name__)


class ExtNetworkML2(plugin.Ml2Plugin,
                    extnet_db_mixin.ExtNetworkDBMixin):
    # List of all the extensions supported by the plugin extension
    extensions_supported = ['extnodeint',
                            'extconnection',
                            'extlink',
                            ]

    def __init__(self):
        for extension in self.extensions_supported:
            self._supported_extension_aliases.append(extension)
        super(ExtNetworkML2, self).__init__()


