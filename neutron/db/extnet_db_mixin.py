from neutron.extensions import extnode
from neutron.extensions import extsegment
from neutron.extensions import extinterface
from neutron.extensions import extlink
from neutron.plugins.ml2.common import extnet_exceptions

from neutron._i18n import _
from neutron.common import exceptions
from neutron.db import extnet_db as models

from oslo_utils import uuidutils
from oslo_log import log as logging
from sqlalchemy.orm import exc as sa_orm_exc
from sqlalchemy.orm import load_only

LOG = logging.getLogger(__name__)


class ExtNetworkDBMixin(extnode.ExtNodePluginInterface,
                        extsegment.ExtSegmentPluginInterface,
                        extinterface.ExtInterfacePluginInterface,
                        extlink.ExtLinkPluginInterface):

    # ------------------------ Auxiliary functions for database operations. -------------------------------------------
    def _admin_check(self, context, action):
        """Admin role check helper."""
        if not context.is_admin:
            reason = _('Cannot %s resource for non admin tenant') % action
            raise exceptions.AdminRequired(reason=reason)

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

    def _make_extnode_dict(self, extnode, interfaces=None):
        """Creates a dictionary to be sent to client API"""
        int_list = []
        node_created = {}
        if interfaces is not None:
            for interface in interfaces:
                inter = {
                    'id': interface.id,
                    'name': interface.name,
                    'type': interface.type
                }
                int_list.append(inter)
            node_created['interfaces'] = int_list
        node_created['id'] = extnode.id
        node_created['name'] = extnode.name
        node_created['type'] = extnode.type
        return node_created

    def _get_existing_extnode(self, context, node_id):
        try:
            node = context.session.query(models.ExtNode).get(node_id)
        except sa_orm_exc.NoResultFound:
            raise extnet_exceptions.ExtNodeNotFound(id=node_id)
        return node

    def _get_interfaces_from_node(self, context, node_id):
        try:
            interfaces = context.session.query(models.ExtNodeInt).filter_by(extnode=node_id).all()
        except sa_orm_exc.NoResultFound:
            raise extnet_exceptions.ExtNodeNotFound(id=node_id)
        return interfaces

    def _extnode_has_connections(self, context, extnode):
        extnode_connections = context.session.query(models.ExtNode, models.ExtConnection)\
            .filter(models.ExtConnection.extnodeint1 == extnode.id)\
            .filter(models.ExtConnection.extnodeint2 == extnode.id)\
            .all()
        return extnode_connections is not None

    def _make_extsegment_dict(self, extsegment):
        extsegment_dict = {
            'id': extsegment['id'],
            'name': extsegment['name'],
            'types_supported': extsegment['types_supported'],
            'ids_pool': extsegment['ids_pool']
        }
        return extsegment_dict

    def _get_existing_extsegment(self, context, segment_id):
        try:
            segment = context.session.query(models.ExtSegment).get(id=segment_id)
        except sa_orm_exc.NoResultFound:
            raise extnet_exceptions.ExtSegmentNotFound(id=segment_id)
        return segment

    def _extsegment_has_links(self, context, extsegment):
        extsegments_links = context.session.query(models.ExtLink).filter_by(extsegment=extsegment.id).all()
        return extsegments_links is not None

    # -------------------- Database operations related with the external interfaces. ----------------------------------
    def delete_extinterface(self, context, id):
        pass

    def create_extinterface(self, context, extinterface):
        pass

    def get_extinterfaces(self, context, filters, fields):
        pass

    def get_extinterface(self, context, id):
        pass

    def update_extinterface(self, context, extinterface):
        pass

    # --------------------- Database operations related with the external nodes. --------------------------------------
    def create_extnode(self, context, extnode):
        LOG.debug("I got here!!!!")
        LOG.info(extnode)
        """Check if the request was made by the admin"""
        self._admin_check(context, 'CREATE')
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
        """Create and return dictionary for the client."""
        return self._make_extnode_dict(node_db, list_int_db)

    def update_extnode(self, context, id, extnode):
        LOG.info(extnode)
        """Check if the request was made by the admin"""
        self._admin_check(context, 'UPDATE')
        node = extnode['extnode']
        with context.session.begin(subtransactions=True):
            node_in_db = self._get_existing_extnode(context, id)
            node_in_db.name = extnode['name']
            node_in_db.type = extnode['type']
            if extnode['add_interfaces'] is not None:
                interfaces = node['add_interfaces']
                for interface in interfaces:
                    int_db = models.ExtNodeInt(
                        id=uuidutils.generate_uuid(),
                        name=interface.get('name'),
                        type=interface.get('type'),
                        extnode=id,
                        extsegment=interface.get('segment_id'))
                    context.session.add(int_db)
            if extnode['rem_interfaces'] is not None:
                interfaces = node['rem_interfaces']
                for interface in interfaces:
                    context.session.query(models.ExtNodeInt).filter_by(id=interface['id']).delete()
            list_int_db = context.session.query(models.ExtNodeInt).filter_by(extnode=id).all()
            context.session.commit()
        return self._make_extnode_dict(node_in_db, list_int_db)

    def get_extnodes(self, context, filters=None, fields=None):
        self._admin_check(context, 'GET')
        extnodes = context.session.query(models.ExtNode)\
            .filter_by(filters)\
            .options(load_only(fields))\
            .all()
        extnodes_list = []
        for extnode in extnodes:
            extnode_dict = self._make_extnode_dict(extnode)
            extnodes_list.append(extnode_dict)
        return {'extnodes': extnodes_list}

    def get_extnode(self, context, id, fields=None):
        self._admin_check(context, 'GET')
        extnode = context.query(models.ExtNode)\
            .filter_by(id=id)\
            .first()
        extnode_int = context.query(models.ExtNodeInt)\
            .filter_by(extnode=id)\
            .all()
        return self._make_extnode_dict(extnode, extnode_int)

    def delete_extnode(self, context, id):
        self._admin_check(context, 'DELETE')
        with context.session.begin(subtransactions=True):
            extnode = self._get_existing_extnode(context, id)
            if self._extnode_has_connections(context, extnode):
                raise extnet_exceptions.ExtnodeHasLinksInUse(id=id)
            context.session.delete(extnode)
        LOG.debug("External node '%s' was deleted.", id)

    # --------------------- Database operations related with the external segments. -----------------------------------
    def create_extsegment(self, context, extsegment):
        self._admin_check(context, 'CREATE')
        segment = extsegment['extsegment']
        with context.session.begin(subtransactions=True):
            segment_db = models.ExtSegment(
                id=uuidutils.generate_uuid(),
                name=extsegment.get('name'),
                types_supported=extsegment.get('types_supported'),
                ids_pool=extsegment.get('ids_pool')
            )
            context.session.add(segment_db)
        return self._make_extsegment_dict(segment_db)

    def update_extsegment(self, context, id, extsegment):
        self._admin_check(context, 'UPDATE')
        segment = extsegment['extsegment']
        with context.session.begin(subtransactions=True):
            segment_in_db = self._get_existing_extsegment(context, extsegment)
            segment_in_db.name = segment['name']
            segment_in_db.types_supported = segment['types_supported']
            segment_in_db.ids_pool = segment['ids_pool']
            context.session.commit()
        return self._make_extsegment_dict(segment_in_db)

    def get_extsegments(self, context, filters, fields):
        self._admin_check(context, 'GET')
        extsegments = context.session.query(models.ExtSegment) \
            .filter_by(filters) \
            .options(load_only(fields)) \
            .all()
        extsegments_list = []
        for extsegment in extsegments:
            extsegment_dict = self._make_extnode_dict(extsegment)
            extsegments_list.append(extsegment_dict)
        return {'extsegments': extsegments_list}

    def get_extsegment(self, context, id):
        self._admin_check(context, 'GET')
        extsegment = context.query(models.ExtSegment) \
            .filter_by(id=id) \
            .first()
        return self._make_extsegment_dict(extsegment)

    def delete_extsegment(self, context, id):
        self._admin_check(context, 'DELETE')
        with context.session.begin(subtransactions=True):
            extsegment = self._get_existing_extsegment(context, id)
            if self._extsegment_has_links(context, extsegment):
                raise extnet_exceptions.ExtSegmentHasLinksInUse(id=id)
            context.session.delete(extsegment)
        LOG.debug("External node '%s' was deleted.", id)

    # --------------------- Database operations related with the external links. --------------------------------------
    def create_extlink(self, context, extlink):
        self._admin_check(context, 'CREATE')
        pass

    def get_extlink(self, context, id, fields):
        self._admin_check(context, 'GET')
        pass

    def update_extlink(self, context, id, extlink):
        self._admin_check(context, 'UPDATE')
        pass

    def get_extlinks(self, context, filters, fields):
        self._admin_check(context, 'GET')
        pass

    def delete_extlink(self, context, id):
        self._admin_check(context, 'DELETE')
        pass
