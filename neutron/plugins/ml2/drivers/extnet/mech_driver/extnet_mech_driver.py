from oslo_config import cfg
from oslo_log import log

from neutron.plugins.ml2 import driver_api as api

LOG = log.getLogger(__name__)

campus_opts = [

    cfg.ListOpt('device_drivers',
                default=[],
                help=_("Ordered list of extension driver entrypoints "
                       "to be loaded from the neutron.ml2.drivers.extnet.device_drivers namespace."))

]

cfg.CONF.register_opts(campus_opts, "ml2_mech_extnet")


class ExtnetMechanismDriver(api.MechanismDriver):

    def initialize(self):
        pass
