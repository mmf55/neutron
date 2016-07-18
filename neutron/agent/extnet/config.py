
from oslo_config import cfg

from neutron._i18n import _

OPTS = [

    cfg.StrOpt('device_configs_path',
               default='/home/mfernandes/drivers_and_configs/',
               help=_("The location on the hard driver where is located the configurations"
                      "for the managed devices on this device controller. (absolute path)"))
]

