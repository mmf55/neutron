
from oslo_config import cfg

default_group = cfg.OptGroup(name='DEFAULT',
                             title='Device controller default options.')

default_opts = [
    cfg.ListOpt('devices', default=None,
                help='List of the devices that this controller configures.')
]
