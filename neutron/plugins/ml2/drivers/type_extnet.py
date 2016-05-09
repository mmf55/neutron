
from oslo_config import cfg
from oslo_log import log

from neutron._i18n import _, _LE, _LI, _LW
from neutron.common import exceptions as exc
from neutron.db import api as db_api
from neutron.db import model_base
from neutron.plugins.common import constants
from neutron.plugins.ml2.drivers import helpers
from neutron.plugins.common import constants as p_const

LOG = log.getLogger(__name__)

campus_opts = [
    # cfg.DictOpt('campus_topology',
    #             default={},
    #             help=_("Dictionary defining the network topology. "
    #                    "Example: "
    #                     "{                                                              "
    #                     "   campus_topology: [{                                         "
    #                     "        cnode: < node_name >,                                  "
    #                     "         csegments: [< csegment_name1 >, < csegment_name2 >]   "
    #                     "    }, {                                                       "
    #                     "        cnode: < node_name >,                                  "
    #                     "        csegments: [< csegment_name1 >, < csegment_name2 >]    "
    #                     "    }]                                                         "
    #                     "}")),

    cfg.ListOpt('network_vlan_ranges',
                default=[],
                help=_("List of <physical_network>:<vlan_min>:<vlan_max> or "
                       "<physical_network> specifying physical_network names "
                       "usable for VLAN provider and tenant networks, as "
                       "well as ranges of VLAN tags on each available for "
                       "allocation to tenant networks.")),

    # cfg.ListOpt('device_drivers',
    #             default=[],
    #             help=_("Ordered list of extension driver entrypoints "
    #                    "to be loaded from the neutron.ml2.drivers.extnet.device_drivers namespace."))
]

cfg.CONF.register_opts(campus_opts, "ml2_type_extnet")


class ExtnetTypeDriver(helpers.BaseTypeDriver):

    def validate_provider_segment(self, segment):
        pass

    def release_segment(self, session, segment):
        pass

    def initialize(self):
        pass

    def is_partial_segment(self, segment):
        pass

    def reserve_provider_segment(self, session, segment):
        pass

    def allocate_tenant_segment(self, session):
        pass

    def get_type(self):
        return p_const.TYPE_CAMPUS
