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

    def create_port_postcommit(self, context):
        super(ExtnetMechanismDriver, self).create_port_postcommit(context)

    def delete_port_precommit(self, context):
        super(ExtnetMechanismDriver, self).delete_port_precommit(context)

    def update_port_precommit(self, context):
        super(ExtnetMechanismDriver, self).update_port_precommit(context)

    def update_port_postcommit(self, context):
        super(ExtnetMechanismDriver, self).update_port_postcommit(context)

    def delete_port_postcommit(self, context):
        super(ExtnetMechanismDriver, self).delete_port_postcommit(context)

    def create_port_precommit(self, context):
        super(ExtnetMechanismDriver, self).create_port_precommit(context)

    def initialize(self):
        pass
