from neutron.plugins.ml2 import plugin
from neutron.db import ext_network_db_mixin

from oslo_log import log as logging

LOG = logging.getLogger(__name__)


class ExtNetworkML2(plugin.Ml2Plugin,
                    ext_network_db_mixin.ExtNetworkDBMixin):

    def create_extnode(self, context, ext_node):
        LOG.debug("I got here!!!!")
        super(ExtNetworkML2, self).create_extnode(context, ext_node)

    def create_extsegment(self, context, ext_segment):
        super(ExtNetworkML2, self).create_extsegment(context, ext_segment)
