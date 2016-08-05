from oslo_config import cfg

netctrl_group = cfg.OptGroup(name='EXTNET_CONTROLLER',
                             title='Network controller default options.')

netctrl_opts = [
    cfg.DictOpt('network_controller_info',
                default='name: OVS,ip_address: 192.168.2.2,netmask: 255.255.255.0,nexthop: 192.168.2.1',
                required=False,
                help='Network controller node name.'),

    cfg.StrOpt('nexthop_ip',
               default='192.168.2.1',
               required=False,
               help='Network controller next hop device.'),

    cfg.DictOpt('device_controllers',
                default="q-agent-notifier: OVS,extnet_agent: ESW1;ESW2;ESW4",
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
