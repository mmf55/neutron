
from oslo_config import cfg

from neutron.plugins.ml2.drivers.extnet.agent.device_controller import api as devapi


class ExtNetDeviceController(devapi.ExtNetDeviceController):

    def __init__(self):
        pass

    def create_segment(self, segment):
        pass

    def show_segment(self, id):
        pass

    def update_segment(self, id, segment):
        pass

    def delete_segment(self, id):
        pass
