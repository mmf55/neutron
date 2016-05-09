
from oslo_config import cfg

default_group = cfg.OptGroup(name='DEFAULT',
                             title='Device controller default options.')

default_opts = [
    cfg.DictOpt('devices', default=None,
                help='Dictionary of the devices that this controller configures.')
]

cfg.CONF.