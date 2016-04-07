from neutron.extensions import extnode
from neutron.extensions import extsegment
from neutron.extensions import extinterface
from neutron.extensions import extlink

from oslo_log import log as logging

LOG = logging.getLogger(__name__)


class ExtNetworkDBMixin(extnode.ExtNodePluginInterface,
                        extsegment.ExtSegmentPluginInterface,
                        extinterface.ExtInterfacePluginInterface,
                        extlink.ExtLinkPluginInterface):
    # -------------------- Database operations related with the external interfaces. ----------------------------------
    def delete_extinterface(self, context, id):
        pass

    def create_extinterface(self, context, ext_interface):
        pass

    def list_extinterface(self, context):
        pass

    def show_extinterface(self, context, id):
        pass

    def update_extinterface(self, context, ext_interface):
        pass

    # --------------------- Database operations related with the external nodes. --------------------------------------
    def create_extnode(self, context, ext_node):
        LOG.debug("I got here!!!!")
        LOG.info(ext_node)

    def update_extnode(self, context, ext_node):
        pass

    def list_extnode(self, context):
        pass

    def show_extnode(self, context, id):
        pass

    def delete_extnode(self, context, id):
        pass

    # --------------------- Database operations related with the external segments. -----------------------------------
    def update_extsegment(self, context, ext_segment):
        pass

    def list_extsegment(self, context):
        pass

    def create_extsegment(self, context, ext_segment):
        pass

    def show_extsegment(self, context, id):
        pass

    def delete_extsegment(self, context, id):
        pass

    # --------------------- Database operations related with the external links. --------------------------------------
    def show_extlink(self, context, id):
        pass

    def update_extlink(self, context, ext_link):
        pass

    def list_extlink(self, context):
        pass

    def create_extlink(self, context, ext_link):
        pass

    def delete_extlink(self, context, id):
        pass
