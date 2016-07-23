from oslo_log import log as logging

from neutron._i18n import _LI
from neutron.db import extport_db_mixin as extport_db
from neutron.extensions import extport
from neutron.plugins.ml2 import driver_api as api

from neutron.db import extnet_db as models

LOG = logging.getLogger(__name__)


class ExtPortExtensionDriver(api.ExtensionDriver,
                             extport_db.ExtPortDBMixin):
    _supported_extension_alias = 'extport'

    def initialize(self):
        LOG.info(_LI("ExtPortExtensionDriver initialization complete"))

    @property
    def extension_alias(self):
        return self._supported_extension_alias

    def process_create_port(self, plugin_context, data, result):
        if data[extport.EXT_INTERFACE_ID]:
            self._process_create_port(plugin_context, data, result)

    def process_update_port(self, plugin_context, data, result):
        if extport.EXT_INTERFACE_ID in data:
            self._process_update_port(plugin_context, data, result)

    def extend_port_dict(self, session, base_model, result):
        LOG.debug('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
        LOG.debug(base_model)
        LOG.debug(hasattr(session, 'query'))
        LOG.debug(result.get('id'))

        extport = session.query(models.ExtPort).filter_by(id=result.get('id')).first()
        LOG.debug(extport)
        if extport:
            result[extport.EXT_INTERFACE_ID] = extport.id
        elif result.get(extport.EXT_INTERFACE_ID) is None:
            result[extport.EXT_INTERFACE_ID] = (extport.EXTENDED_ATTRIBUTES_2_0['ports']
                                                [extport.EXT_INTERFACE_ID]['default'])
