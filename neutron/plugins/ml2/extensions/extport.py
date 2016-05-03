
from oslo_log import log as logging

from neutron._i18n import _LI
from neutron.db import extport_db_mixin as extport_db
from neutron.extensions import extport
from neutron.plugins.ml2 import driver_api as api

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
        if data[extport.EXTPORT] is not None:
            self._process_create_port(plugin_context, data, result)

    def process_update_port(self, plugin_context, data, result):
        if data[extport.EXTPORT] is not None:
            self._process_update_port(plugin_context, data, result)

    def extend_port_dict(self, session, base_model, result):
        # result[extport.EXTPORT] = base_model[extport.EXTPORT]

        if base_model.get('extport') is None:
            result[extport.EXTPORT] = (
                extport.EXTENDED_ATTRIBUTES_2_0['ports']
                [extport.EXTPORT]['default'])
        else:
            result[extport.EXTPORT] = (
                base_model['extport'][extport.EXTPORT])

