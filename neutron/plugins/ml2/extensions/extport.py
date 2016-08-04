from oslo_log import log as logging

from neutron.extensions import extport as extport_dict_ext

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
        if data[extport.EXT_NODE_NAME]:
            result[extport_dict_ext.EXT_NODE_NAME] = data[extport_dict_ext.EXT_NODE_NAME]
        if data[extport.EXT_INTERFACE_NAME]:
            result[extport_dict_ext.EXT_INTERFACE_NAME] = data[extport_dict_ext.EXT_INTERFACE_NAME]
            self._process_create_port(plugin_context, data, result)

    def process_update_port(self, plugin_context, data, result):
        if extport.EXT_NODE_NAME in data:
           self._process_update_port(plugin_context, data, result)
        pass

    def extend_port_dict(self, session, base_model, result):
        if result.get(extport.EXT_NODE_NAME) is None:
            result[extport.EXT_NODE_NAME] = (extport.EXTENDED_ATTRIBUTES_2_0['ports']
                                             [extport.EXT_NODE_NAME]['default'])
        if result.get(extport.EXT_INTERFACE_NAME) is None:
            result[extport.EXT_INTERFACE_NAME] = (extport.EXTENDED_ATTRIBUTES_2_0['ports']
                                                  [extport.EXT_INTERFACE_NAME]['default'])
