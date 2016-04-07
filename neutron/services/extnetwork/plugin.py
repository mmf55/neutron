
from neutron.db import servicetype_db as st_db
from neutron.services import provider_configuration as pconf
from neutron.services import service_base

from neutron.db import ext_network_db_mixin
from neutron.services.extnetwork.common import config
from neutron.services.extnetwork.common import constants

from oslo_log import log as logging

LOG = logging.getLogger(__name__)


def add_provider_configuration(type_manager, service_type):
    type_manager.add_provider_configuration(
        service_type,
        pconf.ProviderConfiguration('ext_network'))


class ExtNetworkPlugin(ext_network_db_mixin.ExtNetworkDBMixin):

    """ Implementation of the Neutron external network NaaS service plugin.

    This class manages the workflow of external network orchestration request/response.
    """

    supported_extension_aliases = ["extnode",
                                   "extsegment",
                                   "extlink",
                                   "extinterface"]

    def __init__(self):
        """Do the initialization for the external network NaaS service plugin here."""
        config.register_ext_network_opts_helper()
        self.service_type_manager = st_db.ServiceTypeManager.get_instance()
        add_provider_configuration(self.service_type_manager, constants.EXT_NET)
        self._load_drivers()
        super(ExtNetworkPlugin, self).__init__()

    def _load_drivers(self):
        """Loads plugin-drivers specified in configuration."""
        self.drivers, self.default_provider = service_base.load_drivers(
            constants.EXT_NET, self)
