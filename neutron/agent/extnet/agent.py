from oslo_config import cfg
from stevedore import driver

from extnet_networkcontroller.device_controller import dev_ctrl

from neutron.common import topics
from neutron import manager
from neutron import context
from neutron.agent import rpc as agent_rpc


class ExtNetDeviceControllerMixin(dev_ctrl.ExtNetDeviceController):
    def initialize(self, config):
        config_dict = dict(device_drivers=config.device_drivers,
                           device_configs_path=config.device_configs_path)
        super(ExtNetDeviceControllerMixin, self).__init__(config_dict)

    def deploy_port(self, interface, segmentation_id, **kwargs):
        return self.load_driver(interface.get('node_name'),
                                interface.get('node_driver')).deploy_port(interface.get('type'),
                                                                          segmentation_id,
                                                                          interface.get('name'),
                                                                          vnetwork=kwargs.get('vnetwork'))

    def deploy_link(self, interface, network_type, segmentation_id, **kwargs):
        return self.load_driver(interface.get('node_name'),
                                interface.get('node_driver')).deploy_link(network_type,
                                                                          interface.get('name'),
                                                                          kwargs.get('remote_ip'),
                                                                          segmentation_id,
                                                                          vnetwork=kwargs.get('vnetwork'))

    def device_controller_name(self):
        return topics.EXTNET_AGENT

    def load_driver(self, device_name, device_driver):
        if device_driver not in self.config.get('device_drivers'):
            return

        return driver.DriverManager(
            namespace='neutron.agent.extnet.device_drivers',
            name=device_driver,
            invoke_on_load=True,
            invoke_args=(device_name, self.config.get('device_configs_path'))
        ).driver


class ExtNetAgent(ExtNetDeviceControllerMixin,
                  manager.Manager):
    def __init__(self, conf=None):
        if conf:
            self.conf = conf
        else:
            self.conf = cfg.CONF

        super(ExtNetAgent, self).__init__()

        self.initialize(conf)

        self._setup_rpc()

    def _setup_rpc(self):

        # RPC network init
        self.context = context.get_admin_context_without_session()
        # Define the listening consumers for the agent
        consumers = [[topics.EXTNET_PORT, topics.CREATE],
                     [topics.EXTNET_LINK, topics.CREATE], ]
        self.connection = agent_rpc.create_consumers([self],
                                                     topics.EXTNET_AGENT,
                                                     consumers,
                                                     start_listening=False)
