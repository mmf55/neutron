from neutron.db import extnet_db
from neutron.extensions import extport as extport_dict_ext
from neutron.plugins.ml2.common import extnet_exceptions

from neutron.db import extnet_db as models

from sqlalchemy.orm import exc as sa_orm_exc
from oslo_log import log as logging

LOG = logging.getLogger(__name__)


class ExtPortDBMixin(object):

    # ----------------------------------------------- Auxiliary functions ----------------------------------------------

    def _make_extport_dict(self, extport, fields=None):
        extport_dict = {
            extport_dict_ext.EXTPORT: {
                'port_id': extport.port_id,
                'access_id': extport.access_id,
                'extnodeint_id': extport.extnodeint_id
            }
        }
        return self._fields(extport_dict, fields)

    def _get_existing_extport(self, context, extport_id):
        try:
            extport = context.session.query(models.ExtPort).get(extport_id)
        except sa_orm_exc.NoResultFound:
            raise extnet_exceptions.ExtPortNotFound(id=extport_id)
        return extport

    def _fields(self, resource, fields):
        """Get fields for the resource for get query."""
        if fields:
            return dict(((key, item) for key, item in resource.items()
                         if key in fields))
        return resource

    # --------------------------------------- Functions that do database operations. -----------------------------------

    def _process_create_port(self, context, data, result):
        LOG.debug(data)
        with context.session.begin(subtransactions=True):
            extport_db = extnet_db.ExtPort(
                port_id=data['id'],
                access_id=data[extport_dict_ext.EXTPORT]['access_id'],
                extnodeint_id=data[extport_dict_ext.EXTPORT]['extnodeint_id']
            )
            context.session.add(extport_db)
        result[extport_dict_ext.EXTPORT] = data[extport_dict_ext.EXTPORT]
        return self._make_extport_dict(extport_db)

    def _process_update_port(self, context, data, result):
        extport_db = self._get_existing_extport(context, data['id'])
        with context.session.begin(subtransactions=True):
            extport_db.access_id = data[extport_dict_ext.EXTPORT]['access_id']
            extport_db.extnodeint_id = data[extport_dict_ext.EXTPORT]['extnodeint_id']
        result[extport_dict_ext.EXTPORT] = data[extport_dict_ext.EXTPORT]
        return self._make_extport_dict(extport_db)
