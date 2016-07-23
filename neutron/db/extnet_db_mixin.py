import itertools

from neutron.extensions import extsegment
from neutron.extensions import extinterface
from neutron.extensions import extlink
from neutron.plugins.ml2.common import extnet_exceptions

from neutron._i18n import _
from neutron.db import extnet_db as models
from neutron.db import extnet_db_query as db_query

from neutron_lib import exceptions
from oslo_utils import uuidutils
from oslo_log import log as logging
from sqlalchemy import or_


LOG = logging.getLogger(__name__)


class ExtNetworkDBMixin(extsegment.ExtSegmentPluginInterface,
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

    def _make_extinterface_dict(self, extinterface, fields=None):
        """Creates a dictionary to be sent to client API"""
        extinterface_dict = {
            'id': extinterface.id,
            'name': extinterface.name,
            'type': extinterface.type,
            'ip_address': extinterface.ip_address,
            'extnode_id': extinterface.extnode_id,
            'extsegment_id': extinterface.extsegment_id
        }
        return self._fields(extinterface_dict, fields)

    def _make_extnode_dict(self, extnode, fields=None):
        extnode_dict = {
            'id': extnode.id,
            'name': extnode.name,
            'ip_address': extnode.ip_address,
        }
        return self._fields(extnode_dict, fields)

    def _get_object_by_id(self, context, model, id):
        try:
            object = context.session.query(model).filter_by(id=id).first()
        except:
            raise extnet_exceptions.ExtNetObjectNotFound(model_name=model.__class__.__name__, id=id)
        return object

    def _extinterface_has_links(self, context, extinterface):
        extinterface_links = context.session.query(models.ExtLink)\
            .filter(or_(models.ExtLink.extinterface1_id == extinterface.id,
                        models.ExtLink.extinterface2_id == extinterface.id))\
            .all()
        return extinterface_links

    def _extnode_has_interfaces(self, context, extnode):
        extnode_interfaces = context.session.query(models.ExtInterface) \
            .filter(models.ExtInterface.extnode_id == extnode.id) \
            .all()
        return extnode_interfaces

    def _make_extsegment_dict(self, extsegment, fields=None):
        extsegment_dict = {
            'id': extsegment.id,
            'type_supported': extsegment.type_supported,
            'name': extsegment.name,
            'ids_available': extsegment.ids_available,
        }
        return self._fields(extsegment_dict, fields)

    def _extsegment_has_links(self, context, extsegment):
        extsegments_links = context.session.query(models.ExtLink).filter_by(extsegment_id=extsegment.id).all()
        return extsegments_links

    def _make_extlink_dict(self, extlink, fields=None):
        """Creates a dictionary to be sent to client API"""
        link_created = {
            'id': extlink.id,
            'name': extlink.name,
            'segmentation_id': extlink.segmentation_id,
            'extinterface1_id': extlink.extinterface1_id,
            'extinterface2_id': extlink.extinterface2_id,
            'network_id': extlink.network_id,
        }
        return self._fields(link_created, fields)

    def _check_if_link_exists(self, context, network_id, extinterface1_id, extinterface2_id):
        link = context.session.query(models.ExtLink) \
            .filter(or_(models.ExtLink.extinterface1_id == extinterface1_id,
                    models.ExtLink.extinterface2_id == extinterface2_id))\
            .filter(models.ExtLink.network_id == network_id)\
            .first()
        return link

    def _fields(self, resource, fields):
        """Get fields for the resource for get query."""
        if fields:
            return dict(((key, item) for key, item in resource.items()
                         if key in fields))
        return resource

    def _make_extport_dict(self, port, fields=None):
        port_created = {
            'id': port.id,
            'extinterface_id': port.extinterface_id,
        }
        return self._fields(port_created, fields)

    def _extinterface_has_extlinks(self, context, interface_id):
        links = context.session.query(models.ExtLink) \
            .filter(or_(models.ExtLink.extinterface1_id == interface_id,
                        models.ExtLink.extinterface2_id == interface_id)) \
            .all()
        return links

    def _check_extsegment_has_links(self, context, extsegment_db):
        interfaces_db = extsegment_db.extinterfaces
        for interfaces_db in interfaces_db:
            links = self._extinterface_has_extlinks(interfaces_db.id)
            if links:
                return True
        return False

    def get_extport(self, context, id, fields=None):
        self._admin_check(context, 'GET')
        port = context.session.query(models.ExtPort) \
            .filter_by(id=id) \
            .first()
        if port:
            return self._make_extport_dict(port, fields=fields)
        else:
            return None

    # --------------------- Database operations related with the external nodes. --------------------------------------

    def create_extnode(self, context, extnode):
        """Check if the request was made by the admin"""
        self._admin_check(context, 'CREATE')
        node = extnode['extnode']
        with context.session.begin(subtransactions=True):
            node_db = models.ExtNode(
                id=uuidutils.generate_uuid(),
                name=node.get('name'),
                ip_address=node.get('ip_address'),
            )
            context.session.add(node_db)
        """Create and return dictionary for the client."""
        return self._make_extnode_dict(node_db)

    def update_extnode(self, context, id, extnode):
        """Check if the request was made by the admin"""
        self._admin_check(context, 'UPDATE')
        node = extnode['extnode']
        with context.session.begin(subtransactions=True):
            node_in_db = self._get_object_by_id(context, models.ExtNode, id)
            node_in_db.name = node['name']
            node_in_db.ip_address = node['ip_address']
        return self._make_extnode_dict(node_in_db)

    def get_extnodes(self, context, filters=None, fields=None):
        self._admin_check(context, 'GET')
        return self._get_collection(context,
                                    models.ExtNode,
                                    self._make_extnode_dict,
                                    filters=filters)

    def get_extnode(self, context, id, fields=None):
        self._admin_check(context, 'GET')
        node = context.session.query(models.ExtNode) \
            .filter_by(id=id) \
            .first()
        return self._make_extnode_dict(node, fields=fields)

    def get_extnode_by_name(self, context, name, fields=None):
        self._admin_check(context, 'GET')
        node = context.session.query(models.ExtNode) \
            .filter_by(name=name) \
            .first()
        return node

    def delete_extnode(self, context, id):
        self._admin_check(context, 'DELETE')
        with context.session.begin(subtransactions=True):
            node = self._get_object_by_id(context, models.ExtNode, id)
            if self._extnode_has_interfaces(context, node):
                raise extnet_exceptions.ExtNodeHasInterfacesInUse(id=id)
            context.session.delete(node)
        LOG.debug("External node '%s' was deleted.", id)

    # --------------------- Database operations related with the external interfaces. ---------------------------------

    def create_extinterface(self, context, extinterface):
        """Check if the request was made by the admin"""
        self._admin_check(context, 'CREATE')
        interface = extinterface['extinterface']
        with context.session.begin(subtransactions=True):
            interface_db = models.ExtInterface(
                id=uuidutils.generate_uuid(),
                name=interface.get('name'),
                type=interface.get('type'),
                ip_address=interface.get('ip_address'),
                extnode_id=interface.get('extnode_id'),
                extsegment_id=interface.get('extsegment_id')
            )
            context.session.add(interface_db)
        """Create and return dictionary for the client."""
        return self._make_extinterface_dict(interface_db)

    def update_extinterface(self, context, id, extinterface):
        """Check if the request was made by the admin"""
        self._admin_check(context, 'UPDATE')
        interface = extinterface['extinterface']
        with context.session.begin(subtransactions=True):
            interface_in_db = self._get_object_by_id(context, models.ExtInterface, id)
            if interface.get('extsegment_id'):
                interface_in_db.extsegment_id = interface['extsegment_id']
            if interface.get('ip_address'):
                interface_in_db.ip_address = interface['ip_address']
        return self._make_extinterface_dict(interface_in_db)

    def get_extinterfaces(self, context, filters=None, fields=None):
        self._admin_check(context, 'GET')
        return self._get_collection(context,
                                    models.ExtInterface,
                                    self._make_extinterface_dict,
                                    filters=filters)

    def get_extinterface(self, context, id, fields=None):
        self._admin_check(context, 'GET')
        interface = context.session.query(models.ExtInterface)\
            .filter_by(id=id)\
            .first()
        return self._make_extinterface_dict(interface, fields=fields)

    def delete_extinterface(self, context, id):
        self._admin_check(context, 'DELETE')
        with context.session.begin(subtransactions=True):
            interface = self._get_object_by_id(context, models.ExtInterface, id)
            if self._extinterface_has_links(context, interface):
                raise extnet_exceptions.ExtInterfaceHasLinksInUse(id=id)
            context.session.delete(interface)
        LOG.debug("External node interface '%s' was deleted.", id)

    # --------------------- Database operations related with the external segments. -----------------------------------
    def create_extsegment(self, context, extsegment):
        self._admin_check(context, 'CREATE')
        segment = extsegment['extsegment']
        with context.session.begin(subtransactions=True):
            segment_db = models.ExtSegment(
                id=uuidutils.generate_uuid(),
                name=segment.get('name'),
                type_supported=segment.get('type_supported'),
                ids_available=segment.get('ids_available'))
            context.session.add(segment_db)
        return self._make_extsegment_dict(segment_db)

    def update_extsegment(self, context, id, extsegment):
        self._admin_check(context, 'UPDATE')
        segment = extsegment['extsegment']
        with context.session.begin(subtransactions=True):
            segment_in_db = self._get_object_by_id(context, models.ExtSegment, id)
            segment_in_db.name = segment['name']
            segment_in_db.type_supported = segment['type_supported']
            segment_in_db.ids_available = segment['ids_available']
        return self._make_extsegment_dict(segment_in_db)

    def get_extsegments(self, context, filters=None, fields=None):
        self._admin_check(context, 'GET')
        return self._get_collection(context,
                                    models.ExtSegment,
                                    self._make_extsegment_dict,
                                    filters=filters)

    def get_extsegment(self, context, id, fields=None):
        self._admin_check(context, 'GET')
        extsegment = context.session.query(models.ExtSegment) \
            .filter_by(id=id) \
            .first()
        return self._make_extsegment_dict(extsegment, fields=fields)

    def delete_extsegment(self, context, id):
        self._admin_check(context, 'DELETE')
        with context.session.begin(subtransactions=True):
            extsegment_db = self._get_object_by_id(context, models.ExtSegment, id)
            if self._check_extsegment_has_links(context, extsegment_db):
                raise extnet_exceptions.ExtSegmentHasLinksInUse(id=id)
            context.session.delete(extsegment_db)
        LOG.debug("External segment '%s' was deleted.", id)

    # --------------------- Database operations related with the external links. --------------------------------------
    def create_extlink(self, context, extlink):
        self._admin_check(context, 'CREATE')
        link = extlink['extlink']
        if self._check_if_link_exists(context,
                                      link.get('network_id'),
                                      link.get('extinterface1_id'),
                                      link.get('extinterface2_id')):
            raise extnet_exceptions.ExtLinkExists(id=link.get('id'))
        with context.session.begin(subtransactions=True):
            link_db = models.ExtLink(
                id=uuidutils.generate_uuid(),
                name=link['name'],
                segmentation_id=link['segmentation_id'],
                extinterface1_id=link['extinterface1_id'],
                extinterface2_id=link['extinterface2_id'],
                network_id=link['network_id'],
            )
            context.session.add(link_db)
        return self._make_extlink_dict(link_db)

    def get_extlink(self, context, id, fields=None):
        self._admin_check(context, 'GET')
        extlink = context.session.query(models.ExtLink)\
            .filter_by(id=id)\
            .first()
        return self._make_extlink_dict(extlink, fields=fields)

    def update_extlink(self, context, id, extlink):
        self._admin_check(context, 'UPDATE')
        link = extlink['extlink']
        with context.session.begin(subtransactions=True):
            link_in_db = self._get_object_by_id(context, models.ExtLink, id)
            link_in_db.name = link['name']
            link_in_db.segmentation_id = link['segmentation_id']
            link_in_db.extinterface1_id = link['extinterface1_id']
            link_in_db.extinterface2_id = link['extinterface2_id']
            link_in_db.network_id = link['network_id']
        return self._make_extlink_dict(link_in_db)

    def get_extlinks(self, context, filters=None, fields=None):
        self._admin_check(context, 'GET')
        return self._get_collection(context,
                                    models.ExtLink,
                                    self._make_extlink_dict,
                                    filters=filters)

    def delete_extlink(self, context, id):
        self._admin_check(context, 'DELETE')
        with context.session.begin(subtransactions=True):
            extlink = self._get_object_by_id(context, models.ExtLink, id)
            context.session.delete(extlink)
        LOG.debug("External link '%s' was deleted.", id)

# -------------------------------------------------------------------------------------------------------------------
