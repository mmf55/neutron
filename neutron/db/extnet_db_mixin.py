from neutron.extensions import extnode
from neutron.extensions import extsegment
from neutron.extensions import extinterface
from neutron.extensions import extlink
from neutron.plugins.ml2.common import extnet_exceptions

from neutron._i18n import _
from neutron.common import exceptions
from neutron.db import extnet_db as models
from neutron.db import extnet_db_query as db_query

from oslo_utils import uuidutils
from oslo_log import log as logging
from sqlalchemy.orm import exc as sa_orm_exc
from sqlalchemy.orm import load_only

LOG = logging.getLogger(__name__)


class ExtNetworkDBMixin(extnode.ExtNodePluginInterface,
                        extsegment.ExtSegmentPluginInterface,
                        extinterface.ExtInterfacePluginInterface,
                        extlink.ExtLinkPluginInterface,
                        db_query.ExtNetworkCommonDbMixin):

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

    def _make_extnode_dict(self, extnode, interfaces=None, fields=None):
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
        return self._fields(node_created, fields)

    def _get_existing_extnode(self, context, node_id):
        try:
            node = context.session.query(models.ExtNode).get(node_id)
        except sa_orm_exc.NoResultFound:
            raise extnet_exceptions.ExtNodeNotFound(id=node_id)
        return node

    def _get_interfaces_from_node(self, context, node_id):
        try:
            interfaces = context.session.query(models.ExtNodeInt).filter_by(extnode_id=node_id).all()
        except sa_orm_exc.NoResultFound:
            raise extnet_exceptions.ExtNodeNotFound(id=node_id)
        return interfaces

    def _extnode_has_connections(self, context, extnode):
        extnode_connections = context.session.query(models.ExtNode, models.ExtConnection)\
            .filter(models.ExtConnection.extnodeint1 == extnode.id)\
            .filter(models.ExtConnection.extnodeint2 == extnode.id)\
            .all()
        return extnode_connections is not None

    def _make_extsegment_dict(self, extsegment, fields=None):
        extsegment_dict = {
            'id': extsegment.id,
            'name': extsegment.name,
            'types_supported': extsegment.types_supported,
            'ids_pool': extsegment.ids_pool
        }
        return self._fields(extsegment_dict, fields)

    def _get_existing_extsegment(self, context, segment_id):
        try:
            segment = context.session.query(models.ExtSegment).get(id=segment_id)
        except sa_orm_exc.NoResultFound:
            raise extnet_exceptions.ExtSegmentNotFound(id=segment_id)
        return segment

    def _extsegment_has_links(self, context, extsegment):
        extsegments_links = context.session.query(models.ExtLink).filter_by(extsegment_id=extsegment.id).all()
        return extsegments_links is not None

    def _make_extlink_dict(self, extlink, connections=None, fields=None):
        """Creates a dictionary to be sent to client API"""
        connections_list = []
        link_created = {}
        if connections is not None:
            for connection in connections:
                conn = {
                    'type': connection.type,
                    'extnodeint1_id': connection.extnodeint1_id,
                    'extnodeint2_id': connection.extnodeint2_id,
                    'extlink_id': connection.extlink_id
                }
                connections_list.append(conn)
            link_created['connections'] = connections_list
        link_created['type'] = extlink.type
        link_created['network_id'] = extlink.network_id
        link_created['overlay_id'] = extlink.overlay_id
        link_created['extsegment_id'] = extlink.extsegment_id
        return self._fields(link_created, fields)

    def _get_existing_extlink(self, context, link_id):
        try:
            link = context.session.query(models.ExtLink).get(link_id)
        except sa_orm_exc.NoResultFound:
            raise extnet_exceptions.ExtNodeNotFound(id=link_id)
        return link

    def _make_extinterface_dict(self, extinterface, fields=None):
        extinterface_dict = {
            'id': extinterface.id,
            'tenant_id': extinterface.tenant_id,
            'extnodeint_id': extinterface.extnodeint_id,
            'network_id': extinterface.network_id
        }
        return self._fields(extinterface_dict, fields)

    def _get_existing_extinterface(self, context, interface_id):
        try:
            interface = context.session.query(models.ExtInterface).get(id=interface_id)
        except sa_orm_exc.NoResultFound:
            raise extnet_exceptions.ExtInterfaceNotFound(id=interface_id)
        return interface

    def _fields(self, resource, fields):
        """Get fields for the resource for get query."""
        if fields:
            return dict(((key, item) for key, item in resource.items()
                         if key in fields))
        return resource

    # -------------------- Database operations related with the external interfaces. ----------------------------------
    def create_extinterface(self, context, extinterface):
        interface = extinterface['extinterface']
        with context.session.begin(subtransactions=True):
            interface_db = models.ExtInterface(
                id=uuidutils.generate_uuid(),
                tenant_id=interface['tenant_id'],
                extnodeint_id=interface['extnodeint_id'],
                network_id=interface['network_id'])
            context.session.add(interface_db)
        return self._make_extinterface_dict(interface_db)

    def update_extinterface(self, context, id, extinterface):
        interface = extinterface['extinterface']
        with context.session.begin(subtransactions=True):
            interface_in_db = self._get_existing_extinterface(context, id)
            interface_in_db.tenant_id = interface['tenant_id']
            interface_in_db.extnodeint_id = interface['extnodeint_id']
            interface_in_db.network_id = interface['network_id']
            context.session.commit()
        return self._make_extinterface_dict(interface_in_db)

    def get_extinterfaces(self, context, filters, fields):
        extinterfaces = context.session.query(models.ExtInterface) \
            .filter_by(filters) \
            .all()
        extinterfaces_list = []
        for extinterface in extinterfaces:
            extinterface_dict = self._make_extinterface_dict(extinterface, fields=fields)
            extinterfaces_list.append(extinterface_dict)
        return extinterfaces_list

    def get_extinterface(self, context, id, fields):
        extinterface = context.query(models.ExtInterface) \
            .filter_by(id=id) \
            .first()
        return self._make_extinterface_dict(extinterface, fields=fields)

    def delete_extinterface(self, context, id):
        with context.session.begin(subtransactions=True):
            extinterface = self._get_existing_extinterface(context, id)
            context.session.delete(extinterface)
        LOG.debug("External node '%s' was deleted.", id)

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
                        extsegment_id=interface.get('segment_id'))
                    context.session.add(int_db)
                    list_int_db.append(int_db)
        """Create and return dictionary for the client."""
        return self._make_extnode_dict(node_db, interfaces=list_int_db)

    def update_extnode(self, context, id, extnode):
        LOG.info(extnode)
        """Check if the request was made by the admin"""
        self._admin_check(context, 'UPDATE')
        node = extnode['extnode']
        with context.session.begin(subtransactions=True):
            node_in_db = self._get_existing_extnode(context, id)
            node_in_db.name = extnode['name']
            node_in_db.type = extnode['type']
            if node['add_interfaces'] is not None:
                interfaces = node['add_interfaces']
                for interface in interfaces:
                    int_db = models.ExtNodeInt(
                        id=uuidutils.generate_uuid(),
                        name=interface.get('name'),
                        type=interface.get('type'),
                        extnode=id,
                        extsegment_id=interface.get('segment_id'))
                    context.session.add(int_db)
            if node['rem_interfaces'] is not None:
                interfaces = node['rem_interfaces']
                for interface in interfaces:
                    context.session.query(models.ExtNodeInt).filter_by(id=interface['id']).delete()
            list_int_db = context.session.query(models.ExtNodeInt).filter_by(extnode_id=id).all()
            context.session.commit()
        return self._make_extnode_dict(node_in_db, interfaces=list_int_db)

    def get_extnodes(self, context, filters=None, fields=None):
        self._admin_check(context, 'GET')
        extnodes = context.session.query(models.ExtNode)\
            .filter_by(filters)\
            .all()
        extnodes_list = []
        for extnode in extnodes:
            extnode_dict = self._make_extnode_dict(extnode, fields=fields)
            extnodes_list.append(extnode_dict)
        return extnodes_list

    def get_extnode(self, context, id, fields=None):
        self._admin_check(context, 'GET')
        extnode = context.query(models.ExtNode)\
            .filter_by(id=id)\
            .first()
        extnode_int = context.query(models.ExtNodeInt)\
            .filter_by(extnode_id=id)\
            .all()
        return self._make_extnode_dict(extnode, interfaces=extnode_int, fields=fields)

    def delete_extnode(self, context, id):
        self._admin_check(context, 'DELETE')
        with context.session.begin(subtransactions=True):
            extnode = self._get_existing_extnode(context, id)
            if self._extnode_has_connections(context, extnode):
                raise extnet_exceptions.ExtNodeHasConnectionsInUse(id=id)
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
                ids_pool=extsegment.get('ids_pool'))
            context.session.add(segment_db)
        return self._make_extsegment_dict(segment_db)

    def update_extsegment(self, context, id, extsegment):
        self._admin_check(context, 'UPDATE')
        segment = extsegment['extsegment']
        with context.session.begin(subtransactions=True):
            segment_in_db = self._get_existing_extsegment(context, id)
            segment_in_db.name = segment['name']
            segment_in_db.types_supported = segment['types_supported']
            segment_in_db.ids_pool = segment['ids_pool']
            context.session.commit()
        return self._make_extsegment_dict(segment_in_db)

    def get_extsegments(self, context, filters, fields):
        self._admin_check(context, 'GET')
        LOG.info(filters)
        # extsegments = context.session.query(models.ExtSegment) \
        #     .filter_by(filters) \
        #     .all()
        # extsegments_list = []
        # for extsegment in extsegments:
        #     extsegment_dict = self._make_extsegment_dict(extsegment, fields=fields)
        #     extsegments_list.append(extsegment_dict)
        return self._get_collection(context,
                                    models.ExtSegment,
                                    self._make_extsegment_dict,
                                    filters=filters)

    def get_extsegment(self, context, id, fields):
        self._admin_check(context, 'GET')
        extsegment = context.query(models.ExtSegment) \
            .filter_by(id=id) \
            .first()
        return self._make_extsegment_dict(extsegment, fields=fields)

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
        link = extlink['extlink']
        list_con_db = []
        with context.session.begin(subtransactions=True):
            link_db = models.ExtLink(
                id=uuidutils.generate_uuid(),
                type=link['type'],
                network_id=link['network_id'],
                overlay_id=link['overlay_id'],
                extsegment_id=link['extsegment_id'])
            context.session.add(link_db)
            if link['add_connections'] is not None:
                connections = link['add_connections']
                for connection in connections:
                    connection_db = models.ExtConnection(
                        type=connection['type'],
                        extnodeint1_id=connection['extnodeint1_id'],
                        extnodeint2_id=connection['extnodeint2_id'],
                        extlink_id=link_db.id)
                    context.session.add(connection_db)
                    list_con_db.append(connection_db)
        return self._make_extlink_dict(link_db, connections=list_con_db)

    def get_extlink(self, context, id, fields):
        self._admin_check(context, 'GET')
        extlink = context.session.query(models.ExtLink)\
            .filter_by(id=id)\
            .first()
        extlink_conn = context.session.query(models.ExtConnection)\
            .filter_by(extlink_id=id)\
            .all()
        return self._make_extlink_dict(extlink, connections=extlink_conn, fields=fields)

    def update_extlink(self, context, id, extlink):
        self._admin_check(context, 'UPDATE')
        link = extlink['extlink']
        with context.session.begin(subtransactions=True):
            link_in_db = self._get_existing_extlink(context, id)
            link_in_db.type = link['type']
            link_in_db.network_id = link['network_id']
            link_in_db.overlay_id = link['overlay_id']
            if link['add_connections'] is not None:
                connections = link['add_connections']
                for connection in connections:
                    connection_db = models.ExtConnection(
                        type=connection['type'],
                        extnodeint1_id=connection['extnodeint1_id'],
                        extnodeint2_id=connection['extnodeint2_id'],
                        extlink_id=link_in_db.id)
                    context.session.add(connection_db)
            if link['rem_connections'] is not None:
                connections = link['rem_connections']
                for connection in connections:
                    context.session.query(models.ExtConnection).filter_by(id=connection['id']).delete()
            list_conn_db = context.session.query(models.ExtConnection).filter_by(extlink_id=id).all()
            context.session.commit()
        return self._make_extlink_dict(link_in_db, connections=list_conn_db)

    def get_extlinks(self, context, filters, fields):
        self._admin_check(context, 'GET')
        extlinks = context.session.query(models.ExtLink) \
            .filter_by(filters) \
            .options(load_only(fields)) \
            .all()
        extlinks_list = []
        for extlink in extlinks:
            extlinks_dict = self._make_extlink_dict(extlink, fields=fields)
            extlinks_list.append(extlinks_dict)
        return extlinks_list

    def delete_extlink(self, context, id):
        self._admin_check(context, 'DELETE')
        with context.session.begin(subtransactions=True):
            extlink = self._get_existing_extlink(context, id)
            context.session.delete(extlink)
        LOG.debug("External link '%s' was deleted.", id)
