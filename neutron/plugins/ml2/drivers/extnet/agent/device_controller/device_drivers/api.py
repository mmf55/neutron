import abc

import six


@six.add_metaclass(abc.ABCMeta)
class ExtNetDeviceDriverBase(object):

    @abc.abstractmethod
    def initialize(self, device):
        pass

    @abc.abstractmethod
    def get_interface_details(self, int_name):\
        pass

    @abc.abstractmethod
    def get_int_ip(self, int_name):
        pass


@six.add_metaclass(abc.ABCMeta)
class ExtNetDDVlanSupport(object):

    @abc.abstractmethod
    def associate_int_to_vlan(self, int_name, vlan_id):
        pass

    @abc.abstractmethod
    def deassociate_int_from_vlan(self, int_name, vlan_id):
        pass

    @abc.abstractmethod
    def set_int_as_trunk(self, int_name):
        pass

    @abc.abstractmethod
    def unset_int_as_trunk(self, int_name):
        pass

    @abc.abstractmethod
    def add_vlan_id_to_trunk(self, int_name, vlan_id):
        pass

    @abc.abstractmethod
    def remove_vlan_id_from_trunk(self, int_name, vlan_id):
        pass


@six.add_metaclass(abc.ABCMeta)
class ExtNetDDGRESupport(object):

    @abc.abstractmethod
    def create_tun_int(self, int_name, tun_int, tun_ip):
        pass

    @abc.abstractmethod
    def delete_tun_int(self, int_name, tun_int):
        pass



