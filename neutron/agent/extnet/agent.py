import imp
import os
import json

from oslo_config import cfg
from oslo_log import log as logging
from stevedore import driver

from extnet_networkcontroller.device_controller import dev_ctrl

from neutron.common import topics
from neutron import manager
from neutron import context
from neutron.agent import rpc as agent_rpc

LOG = logging.getLogger(__name__)


# This class holds the main logic of the external devices device controller.
class ExtNetDeviceControllerMixin(object):
    def initialize(self, config):
        self.config_dict = dict(device_drivers=config.device_drivers,
                                device_configs_path=config.device_configs_path)
        super(ExtNetDeviceControllerMixin, self).__init__()

    def deploy_port(self, ctxt, interface, node, segmentation_id, **kwargs):
        return self.load_driver(node).deploy_port(interface.get('type'),
                                                  interface.get('name'),
                                                  segmentation_id,
                                                  vnetwork=kwargs.get('vnetwork'))

    def undeploy_port(self, ctxt, interface, node, segmentation_id, **kwargs):
        return self.load_driver(node).undeploy_port(interface.get('type'),
                                                    interface.get('name'),
                                                    segmentation_id,
                                                    vnetwork=kwargs.get('vnetwork'))

    def deploy_link(self, ctxt, interface, node, segmentation_id, network_type, **kwargs):
        LOG.debug("Deploy_link on %s" % interface.get('name'))
        return self.load_driver(node).deploy_link(network_type,
                                                  interface.get('name'),
                                                  kwargs.get('remote_ip'),
                                                  segmentation_id,
                                                  vnetwork=kwargs.get('vnetwork'))

    def undeploy_link(self, ctxt, interface, node, segmentation_id, network_type, **kwargs):
        return self.load_driver(node).undeploy_link(network_type,
                                                    interface.get('type'),
                                                    interface.get('name'),
                                                    segmentation_id,
                                                    vnetwork=kwargs.get('vnetwork'))

    def device_controller_name(self):
        return topics.EXTNET_AGENT

    def load_driver(self, node):
        node_name = node.get('name')
        node_ip_address = node.get('ip_address')
        with open(os.path.join(self.config_dict.get('device_configs_path'), node_name + '.json')) as device_json:
            config_dict = json.load(device_json)
        dev_drv_string = config_dict.get('device_driver')
        name, module_path = dev_drv_string.split(':')

        mod = imp.load_source(name.lower(), module_path)
        Class = getattr(mod, name)
        return Class(node_name, node_ip_address, self.config_dict.get('device_configs_path'))

        # def load_driver2(self, device_name, device_driver):
        #     for driver_str in self.config_dict.get('device_drivers'):
        #         name, module_path = driver_str.split(':')
        #         if device_driver.lower() == name.lower():
        #             mod = imp.load_source(name.lower(), module_path)
        #             Class = getattr(mod, name)
        #             return Class(device_name, self.config_dict.get('device_configs_path'))
        #         return


# This class do the necessary setup for the external devices device controller to be launched as a neutron agent.
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
                     [topics.EXTNET_LINK, topics.CREATE],
                     [topics.EXTNET_PORT, topics.DELETE],
                     [topics.EXTNET_LINK, topics.DELETE], ]
        self.connection = agent_rpc.create_consumers([self],
                                                     topics.EXTNET_AGENT,
                                                     consumers,
                                                     start_listening=True)
