from neutron.db import extnet_db
from neutron.extensions import extport


class ExtPortDBMixin(object):

    # ----------------------------------------------- Auxiliary funtions -----------------------------------------------

    def _make_extport_dict(self, extport, fields=None):
        extport_dict = {
            'port_id': extport.port_id,
            'access_id': extport.access_id,
            'extnodeint_id': extport.extnodeint_id
        }
        return self._fields(extport_dict, fields)

    def _fields(self, resource, fields):
        """Get fields for the resource for get query."""
        if fields:
            return dict(((key, item) for key, item in resource.items()
                         if key in fields))
        return resource

    # --------------------------------------- Funtions that do database operations. ------------------------------------

    def _process_create_port(self, context, data, result):
        with context.session.begin(subtransactions=True):
            extport_db = extnet_db.ExtPort(
                port_id=data['id'],
                access_id=data['access_id'],
                extnodeint_id=data['extnodeint_id']
            )
            context.session.add(extport_db)
        result[extport.EXTPORT] = data[extport.EXTPORT]
        result['access_id'] = data['access_id']
        result['extnodeint_id'] = data['extnodeint_id']
        return self._make_extport_dict(extport_db)

    def _process_update_port(self):
        pass
