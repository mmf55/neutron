
from oslo_config import cfg

from neutron._i18n import _

OPTS = [
    cfg.ListOpt('device_drivers',
                default='Cisco3700:/home/mfernandes/drivers_and_configs/cisco3700.py',
                help=_("Device drivers available on this device controller.")
                ),
    cfg.StrOpt('device_configs_path',
               default='',
               help=_("The location on the hard driver where is located the configurations"
                      "for the managed devices on this device controller. (absolute path)"))
]

