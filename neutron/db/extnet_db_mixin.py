from neutron.extensions import extconnection
from neutron.extensions import extnodeint
from neutron.extensions import extlink
from neutron.plugins.ml2.common import extnet_exceptions

from neutron._i18n import _
from neutron.db import extnet_db as models
from neutron.db import extnet_db_query as db_query

from neutron_lib import exceptions
from oslo_utils import uuidutils
from oslo_log import log as logging
from sqlalchemy.orm import exc as sa_orm_exc

LOG = logging.getLogger(__name__)


class ExtNetworkDBMixin(extconnection.ExtConnectionPluginInterface,
                        extnodeint.ExtNodeIntPluginInterface,
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

    def _make_extnodeint_dict(self, extnodeint, fields=None):
        """Creates a dictionary to be sent to client API"""
        extnodeint_dict = {
            'id': extnodeint.id,
            'name': extnodeint.name,
            'type': extnodeint.type,
            'extnodename': extnodeint.extnodename
        }
        return self._fields(extnodeint_dict, fields)

    def _get_existing_extnodeint(self, context, node_id):
        try:
            node = context.session.query(models.ExtNodeInt).get(node_id)
        except sa_orm_exc.NoResultFound:
            raise extnet_exceptions.ExtNodeIntNotFound(id=node_id)
        return node

    def _extnodeint_has_connections(self, context, extnodeint):
        extnode_connections = context.session.query(models.ExtConnection)\
            .filter(models.ExtConnection.extnodeint1_id == extnodeint.id)\
            .filter(models.ExtConnection.extnodeint2_id == extnodeint.id)\
            .all()
        return extnode_connections

    def _make_extconnection_dict(self, extconnection, fields=None):
        extconnection_dict = {
            'id': extconnection.id,
            'types_supported': extconnection.types_supported,
            'ids_pool': extconnection.ids_pool,
            'extnodeint1_id': extconnection.extnodeint1_id,
            'extnodeint2_id': extconnection.extnodeint2_id
        }
        return self._fields(extconnection_dict, fields)

    def _get_existing_extconnection(self, context, extconnection_id):
        try:
            connection = context.session.query(models.ExtConnection).get(extconnection_id)
        except sa_orm_exc.NoResultFound:
            raise extnet_exceptions.ExtConnectionNotFound(id=extconnection_id)
        return connection

    def _extconnection_has_links(self, context, extconnection):
        extsegments_links = context.session.query(models.ExtLink).filter_by(extconnection_id=extconnection.id).all()
        return extsegments_links

    def _make_extlink_dict(self, extlink, fields=None):
        """Creates a dictionary to be sent to client API"""
        connections_list = []
        link_created = {
            'id': extlink.id,
            'type': extlink.type,
            'overlay_id': extlink.overlay_id,
            'extport_id': extlink.extport_id,
            'extconnection_id': extlink.extconnection_id
        }
        return self._fields(link_created, fields)

    def _get_existing_extlink(self, context, link_id):
        try:
            link = context.session.query(models.ExtLink).get(link_id)
        except sa_orm_exc.NoResultFound:
            raise extnet_exceptions.ExtNodeNotFound(id=link_id)
        return link

    def _check_if_conn_exists(self, context, extnodeint1_id, extnodeint2_id):
        connection = context.session.query(models.ExtConnection) \
            .filter(models.ExtConnection.extnodeint1_id == extnodeint1_id and
                    models.ExtConnection.extnodeint2_id == extnodeint2_id) \
            .first()
        return connection

    def _fields(self, resource, fields):
        """Get fields for the resource for get query."""
        if fields:
            return dict(((key, item) for key, item in resource.items()
                         if key in fields))
        return resource

    # --------------------- Database operations related with the external nodes. --------------------------------------
    def create_extnodeint(self, context, extnodeint):
        """Check if the request was made by the admin"""
        self._admin_check(context, 'CREATE')
        node = extnodeint['extnodeint']
        with context.session.begin(subtransactions=True):
            node_db = models.ExtNodeInt(
                id=uuidutils.generate_uuid(),
                name=node.get('name'),
                type=node.get('type'),
                extnodename=node.get('extnodename'))
            context.session.add(node_db)
        """Create and return dictionary for the client."""
        return self._make_extnodeint_dict(node_db)

    def update_extnodeint(self, context, id, extnodeint):
        """Check if the request was made by the admin"""
        self._admin_check(context, 'UPDATE')
        node_int = extnodeint['extnodeint']
        with context.session.begin(subtransactions=True):
            node_in_db = self._get_existing_extnodeint(context, id)
            node_in_db.name = node_int['name']
            node_in_db.type = node_int['type']
            node_in_db.extnodename = node_int['extnodename']
        return self._make_extnodeint_dict(node_in_db)

    def get_extnodeints(self, context, filters=None, fields=None):
        self._admin_check(context, 'GET')
        return self._get_collection(context,
                                    models.ExtNodeInt,
                                    self._make_extnodeint_dict,
                                    filters=filters)

    def get_extnodeint(self, context, id, fields=None):
        self._admin_check(context, 'GET')
        extnode_int = context.session.query(models.ExtNodeInt)\
            .filter_by(id=id)\
            .first()
        return self._make_extnodeint_dict(extnode_int, fields=fields)

    def delete_extnodeint(self, context, id):
        self._admin_check(context, 'DELETE')
        with context.session.begin(subtransactions=True):
            extnode_int = self._get_existing_extnodeint(context, id)
            if self._extnodeint_has_connections(context, extnode_int):
                raise extnet_exceptions.ExtNodeIntHasConnectionsInUse(id=id)
            context.session.delete(extnode_int)
        LOG.debug("External node interface '%s' was deleted.", id)

    # --------------------- Database operations related with the external segments. -----------------------------------
    def create_extconnection(self, context, extconnection):
        self._admin_check(context, 'CREATE')
        connection = extconnection['extconnection']
        if self._check_if_conn_exists(context, connection['extnodeint1_id'], connection['extnodeint2_id']):
            raise extnet_exceptions.ExtConnectionsExists
        with context.session.begin(subtransactions=True):
            connection_db = models.ExtConnection(
                id=uuidutils.generate_uuid(),
                types_supported=connection.get('types_supported'),
                ids_pool=connection.get('ids_pool'),
                extnodeint1_id=connection.get('extnodeint1_id'),
                extnodeint2_id=connection.get('extnodeint2_id'))
            context.session.add(connection_db)
        return self._make_extconnection_dict(connection_db)

    def update_extconnection(self, context, id, extsegment):
        self._admin_check(context, 'UPDATE')
        connection = extconnection['extconnection']
        with context.session.begin(subtransactions=True):
            connection_in_db = self._get_existing_extconnection(context, id)
            connection_in_db.types_supported = connection['types_supported']
            connection_in_db.ids_pool = connection['ids_pool']
            connection_in_db.extnodeint1_id = connection['extnodeint1_id']
            connection_in_db.extnodeint2_id = connection['extnodeint2_id']
        return self._make_extconnection_dict(connection_in_db)

    def get_extconnections(self, context, filters, fields):
        self._admin_check(context, 'GET')
        return self._get_collection(context,
                                    models.ExtConnection,
                                    self._make_extconnection_dict,
                                    filters=filters)

    def get_extconnection(self, context, id, fields):
        self._admin_check(context, 'GET')
        extconnection = context.session.query(models.ExtConnection) \
            .filter_by(id=id) \
            .first()
        return self._make_extconnection_dict(extconnection, fields=fields)

    def delete_extconnection(self, context, id):
        self._admin_check(context, 'DELETE')
        with context.session.begin(subtransactions=True):
            extconnection_db = self._get_existing_extconnection(context, id)
            if self._extconnection_has_links(context, extconnection_db):
                raise extnet_exceptions.ExtConnectionHasLinksInUse(id=id)
            context.session.delete(extconnection_db)
        LOG.debug("External connection '%s' was deleted.", id)

    # --------------------- Database operations related with the external links. --------------------------------------
    def create_extlink(self, context, extlink):
        self._admin_check(context, 'CREATE')
        link = extlink['extlink']
        with context.session.begin(subtransactions=True):
            link_db = models.ExtLink(
                id=uuidutils.generate_uuid(),
                type=link['type'],
                overlay_id=link['overlay_id'],
                extport_id=link['extport_id'],
                extconnection_id=link['extconnection_id'])
            context.session.add(link_db)
        return self._make_extlink_dict(link_db)

    def get_extlink(self, context, id, fields):
        self._admin_check(context, 'GET')
        extlink = context.session.query(models.ExtLink)\
            .filter_by(id=id)\
            .first()
        return self._make_extlink_dict(extlink, fields=fields)

    def update_extlink(self, context, id, extlink):
        self._admin_check(context, 'UPDATE')
        link = extlink['extlink']
        with context.session.begin(subtransactions=True):
            link_in_db = self._get_existing_extlink(context, id)
            link_in_db.type = link['type']
            link_in_db.overlay_id = link['overlay_id']
            link_in_db.extport_id = link['extport_id']
            link_in_db.extconnection_id = link['extconnection_id']
        return self._make_extlink_dict(link_in_db)

    def get_extlinks(self, context, filters, fields):
        self._admin_check(context, 'GET')
        return self._get_collection(context,
                                    models.ExtLink,
                                    self._make_extlink_dict,
                                    filters=filters)

    def delete_extlink(self, context, id):
        self._admin_check(context, 'DELETE')
        with context.session.begin(subtransactions=True):
            extlink = self._get_existing_extlink(context, id)
            context.session.delete(extlink)
        LOG.debug("External link '%s' was deleted.", id)
