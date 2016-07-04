from oslo_config import cfg

netctrl_group = cfg.OptGroup(name='EXTNET_CONTROLLER',
                             title='Network controller default options.')

netctrl_opts = [
    cfg.DictOpt('device_controllers',
                required=False,
                help='Device controller name.'),
    cfg.StrOpt('network_mapper_namespace',
               required=False,
               help=''),
    cfg.StrOpt('network_mapper_class',
               required=False,
               help=''),
]

cfg.CONF.register_group(netctrl_group)
cfg.CONF.register_opts(netctrl_opts, netctrl_group)

