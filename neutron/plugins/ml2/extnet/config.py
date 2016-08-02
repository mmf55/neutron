from oslo_config import cfg

netctrl_group = cfg.OptGroup(name='EXTNET_CONTROLLER',
                             title='Network controller default options.')

netctrl_opts = [
    cfg.StrOpt('net_ctrl_node_name',
               default='OVS',
               required=False,
               help='Network controller node name.'),

    cfg.DictOpt('device_controllers',
                default="q-agent-notifier: OVS,extnet_agent: ESW1;ESW2",
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

