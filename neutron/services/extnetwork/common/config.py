
from oslo_config import cfg
from oslo_log import log as logging
from neutron._i18n import _, _LE, _LI, _LW

LOG = logging.getLogger(__name__)

EXT_NET_OPTS = [
    cfg.IntOpt('periodic_monitoring_interval',
               default=5,
               help=_('Periodic interval at which the plugin '
                      'checks for the monitoring external network agent'))
]


def register_ext_network_opts_helper():
    cfg.CONF.register_opts(EXT_NET_OPTS)
