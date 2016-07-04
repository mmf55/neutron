
from oslo_config import cfg

from neutron._i18n import _

OPTS = [
    cfg.ListOpt('device_drivers',
                help=_("Device drivers available on this device controller.")
                ),
    cfg.StrOpt('device_configs_path',
               help=_("The location on the hard driver where is located the configurations"
                      "for the managed devices on this device controller. (absolute path)"))
]

