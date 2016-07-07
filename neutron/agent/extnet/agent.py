import imp

from oslo_config import cfg
from oslo_log import log as logging
from stevedore import driver

from extnet_networkcontroller.device_controller import dev_ctrl

from neutron.common import topics
from neutron import manager
from neutron import context
from neutron.agent import rpc as agent_rpc

LOG = logging.getLogger(__name__)


class ExtNetDeviceControllerMixin(object):
    def initialize(self, config):
        self.config_dict = dict(device_drivers=config.device_drivers,
                                device_configs_path=config.device_configs_path)
        super(ExtNetDeviceControllerMixin, self).__init__()

    def deploy_port(self, ctxt, interface, segmentation_id, **kwargs):
        return self.load_driver(interface.get('node_name'),
                                interface.get('node_driver')).deploy_port(interface.get('type'),
                                                                          segmentation_id,
                                                                          interface.get('name'),
                                                                          vnetwork=kwargs.get('vnetwork'))

    def deploy_link(self, ctxt, interface, segmentation_id, network_type, **kwargs):
        LOG.debug("Deploy_link on %s" % interface.get('name'))
        return self.load_driver(interface.get('node_name'),
                                interface.get('node_driver')).deploy_link(network_type,
                                                                          interface.get('name'),
                                                                          kwargs.get('remote_ip'),
                                                                          segmentation_id,
                                                                          vnetwork=kwargs.get('vnetwork'))

    def device_controller_name(self):
        return topics.EXTNET_AGENT

    def load_driver(self, device_name, device_driver):
        for driver_str in self.config_dict.get('device_drivers'):
            name, module_path = driver_str.split(':')
            if device_driver.lower() == name.lower():
                mod = imp.load_source(name.lower(), module_path)
                Class = getattr(mod, name)
                return Class(device_name, self.config_dict.get('device_configs_path'))
            return


class ExtNetAgent(ExtNetDeviceControllerMixin,
                  manager.Manager):
    def __init__(self, host, conf=None):
        if conf:
            self.conf = conf
        else:
            self.conf = cfg.CONF

        super(ExtNetAgent, self).__init__(host)

        self.initialize(self.conf)

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
                                                     start_listening=True)
