import abc
import six


@six.add_metaclass(abc.ABCMeta)
class TopologyDicoveryApi(object):

    @abc.abstractmethod
    def get_devices_info(self, ip_address, **kwargs):
        pass


@six.add_metaclass(abc.ABCMeta)
class TopoDiscMechanismApi(object):

    @abc.abstractmethod
    def connect(self, hostname, **kwargs):
        pass

    @abc.abstractmethod
    def get_node_name(self):
        pass

    @abc.abstractmethod
    def get_node_interfaces_up(self):
        pass

    @abc.abstractmethod
    def get_node_info_dict(self):
        pass

