from neutron.extensions import extnode
from neutron.extensions import extsegment
from neutron.extensions import extinterface
from neutron.extensions import extlink

from neutron._i18n import _
from neutron.common import exceptions
from neutron.db import extnet_db as models

from oslo_utils import uuidutils
from oslo_log import log as logging

LOG = logging.getLogger(__name__)


class ExtNetworkDBMixin(extnode.ExtNodePluginInterface,
                        extsegment.ExtSegmentPluginInterface,
                        extinterface.ExtInterfacePluginInterface,
                        extlink.ExtLinkPluginInterface):
    def _get_tenant_id_for_create(self, context, resource):
        """Get tenant id for creation of resources."""
        if context.is_admin and 'tenant_id' in resource:
            tenant_id = resource['tenant_id']
        elif ('tenant_id' in resource and
                      resource['tenant_id'] != context.tenant_id):
            reason = _('Cannot create resource for another tenant')
            raise exceptions.AdminRequired(reason=reason)
        else:
            tenant_id = context.tenant_id
        return tenant_id

    def _make_extnode_dict(self, extnode, interfaces):
        int_list = []
        for interface in interfaces:
            inter = {
                'id': interface.id,
                'name': interface.name,
                'type': interface.type
            }
            int_list.append(inter)
        node_created = {
            'id': extnode.id,
            'name': extnode.name,
            'type': extnode.type,
            'interfaces': int_list
        }
        return node_created

    # -------------------- Database operations related with the external interfaces. ----------------------------------
    def delete_extinterface(self, context, id):
        pass

    def create_extinterface(self, context, extinterface):
        pass

    def list_extinterface(self, context):
        pass

    def show_extinterface(self, context, id):
        pass

    def update_extinterface(self, context, extinterface):
        pass

    # --------------------- Database operations related with the external nodes. --------------------------------------
    def create_extnode(self, context, extnode):
        LOG.debug("I got here!!!!")
        LOG.info(extnode)
        node = extnode['extnode']
        list_int_db = []
        with context.session.begin(subtransactions=True):
            node_db = models.ExtNode(
                id=uuidutils.generate_uuid(),
                name=node.get('name'),
                type=node.get('type'))
            context.session.add(node_db)
            if node['add_interfaces'] is not None:
                interfaces = node['add_interfaces']
                for interface in interfaces:
                    int_db = models.ExtNodeInt(
                        id=uuidutils.generate_uuid(),
                        name=interface.get('name'),
                        type=interface.get('type'),
                        extnode=node_db.get('id'),
                        extsegment=interface.get('segment_id'))
                    context.session.add(int_db)
                    list_int_db.append(int_db)
        return self._make_extnode_dict(node_db, list_int_db)

    def update_extnode(self, context, extnode):
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
