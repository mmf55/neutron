from oslo_config import cfg

netctrl_group = cfg.OptGroup(name='EXTNET_CONTROLLER',
                             title='Network controller default options.')

netctrl_opts = [
    cfg.StrOpt('name',
               default='OVS',
               required=False,
               help='Network controller name.'),

    cfg.StrOpt('ip_address',
               # default='10.0.4.2',
               required=False,
               help='Network controller IP address.'),

    cfg.StrOpt('netmask',
               # default='255.255.255.0',
               required=False,
               help='Network mask of the network controller.'),

    cfg.StrOpt('ids_available',
               default='11:20',
               required=False,
               help='Networks IDs available on the first hop segment.'),

    cfg.StrOpt('nexthop_ip',
               # default='192.168.2.1',
               default='10.0.4.1',
               required=False,
               help='Next hop device IP address for access by the network controller.'),

    cfg.StrOpt('nexthop_name',
               default='ESW2',
               required=False,
               help='Next hop device name connected to network controller.'),

    cfg.DictOpt('nexthop_interface',
                default='name: FastEthernet1/1,ip_address: ''',
                required=False,
                help='Next hop device interface connected to network controller.'),

    cfg.DictOpt('device_controllers',
                default="q-agent-notifier: OVS,extnet_agent: ESW1;ESW2;ESW4",
                required=False,
                help='Device controller available on the network controller.'),
]

cfg.CONF.register_group(netctrl_group)
cfg.CONF.register_opts(netctrl_opts, netctrl_group)
