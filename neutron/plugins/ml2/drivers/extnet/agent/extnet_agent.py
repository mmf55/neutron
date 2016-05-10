
from oslo_config import cfg
from oslo_log import log as logging
import oslo_messaging
from oslo_service import service

from neutron.plugins.ml2.drivers.agent import _agent_manager_base as amb
from neutron.plugins.ml2.drivers.extnet.agent.device_controller import device_controller as dc


class ExtNetAgentManager(amb.CommonAgentManagerBase):
    def delete_arp_spoofing_protection(self, devices):
        pass

    def plug_interface(self, network_id, network_segment, device, device_owner):
        pass

    def get_devices_modified_timestamps(self, devices):
        pass

    def ensure_port_admin_state(self, device, admin_state_up):
        pass

    def delete_unreferenced_arp_protection(self, current_devices):
        pass

    def get_agent_id(self):
        pass

    def get_agent_configurations(self):
        pass

    def get_rpc_callbacks(self, context, agent, sg_agent):
        pass

    def get_extension_driver_type(self):
        pass

    def setup_arp_spoofing_protection(self, device, device_details):
        pass

    def get_rpc_consumers(self):
        pass

    def get_all_devices(self):
        pass


class ExtNetRPCCallback(amb.CommonAgentManagerRpcCallBackBase,
                        dc.ExtNetDeviceController):

    target = oslo_messaging.Target(version='1.4')

    def security_groups_provider_updated(self, context, **kwargs):
        pass

    def security_groups_rule_updated(self, context, **kwargs):
        pass

    def security_groups_member_updated(self, context, **kwargs):
        pass

