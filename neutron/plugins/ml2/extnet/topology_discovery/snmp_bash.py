import re
import binascii

from easysnmp import Session
from easysnmp import exceptions

from extnet_networkcontroller.topology_discovery import topology_discovery_api
from extnet_networkcontroller.common import utils

OID_NODE_NAME = 'iso.3.6.1.2.1.1.5.0.'
OID_NODE_IFDESCR = 'iso.3.6.1.2.1.2.2.1.2.'
OID_NODE_IFOPERSTATUS = 'iso.3.6.1.2.1.2.2.1.8.'
OID_NODE_IPADDRESS = 'iso.3.6.1.2.1.4.20.1.2.'
OID_NODE_NETMASKS = 'iso.3.6.1.2.1.4.20.1.3.'
OID_NODE_NEXTHOPS = 'iso.3.6.1.2.1.4.22.1.3.'
OID_NODES_CONNECTED = 'enterprises.9.9.23.1.2.1.1.6.'
OID_INTS_CONNECTED = 'enterprises.9.9.23.1.2.1.1.7.'
OID_NODE_INTS_TRUNKING = 'enterprises.9.9.46.1.6.1.1.14.'
OID_NODE_INTS_TRUNKS = 'enterprises.9.9.46.1.6.1.1.4.'

PORT = 23
PASSWORD = 'pass'


class SnmpCisco(topology_discovery_api.TopoDiscMechanismApi):
    def connect(self, hostname, **kwargs):
        self.hostname = hostname
        self.session = Session(hostname=hostname,
                               community=kwargs['community'],
                               version=kwargs['version'])

    def get_node_name(self):
        try:
            return self.session.get(OID_NODE_NAME).value

        except exceptions.EasySNMPTimeoutError:
            return None

    def get_node_interfaces_up(self):
        int_list = []
        p1 = re.compile("^FastEthernet")
        p2 = re.compile("^Vlan")
        all_ints_list = [x for x in self.session.walk(OID_NODE_IFDESCR)
                         if (p1.match(x.value) or p2.match(x.value)) and
                         self.session.get(OID_NODE_IFOPERSTATUS + x.oid_index).value == '1']

        vlan_ints_list = [x for x in self.session.walk(OID_NODE_IFDESCR)
                          if p2.match(x.value) and self.session.get(OID_NODE_IFOPERSTATUS + x.oid_index).value == '1']

        ips_list = [(x.value, x.oid_index) for x in self.session.walk(OID_NODE_IPADDRESS)]
        netmasks_list = [(x.value, x.oid_index) for x in self.session.walk(OID_NODE_NETMASKS)]

        connected_node_names_list = [(x.value, x.oid.split(OID_NODES_CONNECTED)[1].split('.')[0])
                                     for x in self.session.walk(OID_NODES_CONNECTED)]

        connected_interfaces_list = [(x.value, x.oid.split(OID_INTS_CONNECTED)[1].split('.')[0])
                                     for x in self.session.walk(OID_INTS_CONNECTED)]

        ints_trunking_list = [(x.value, x.oid.split(OID_NODE_INTS_TRUNKING)[1].split('.')[0])
                              for x in self.session.walk(OID_NODE_INTS_TRUNKING)]

        ints_trunks_list = [(x.value, x.oid.split(OID_NODE_INTS_TRUNKS)[1].split('.')[0])
                            for x in self.session.walk(OID_NODE_INTS_TRUNKS)]

        print self.session.walk(OID_NODE_INTS_TRUNKS)

        # print ips_list
        for interface in all_ints_list:
            # print interface
            ip_address = next((x[1] for x in ips_list if x[0] == interface.oid_index), None)
            netmask = next((x[0] for x in netmasks_list if x[1] == ip_address), None)
            trunking = next((x[0] for x in ints_trunking_list if x[1] == interface.oid_index), None)
            # print ip_address
            next_hops = [x.value for x in self.session.walk(OID_NODE_NEXTHOPS + interface.oid_index)
                         if ip_address != x.value]
            # print next_hops
            ids_available = None
            if trunking == '1':
                trunks = next((x[0] for x in ints_trunks_list if x[1] == interface.oid_index), None)
                ids_available = self._get_trunk_ids_available(trunks, vlan_ints_list)

            dev_connected = self._get_devs_connected(interface.oid_index,
                                                     connected_node_names_list,
                                                     connected_interfaces_list)
            d = dict(name=interface.value,
                     ip_address=ip_address,
                     netmask=netmask,
                     next_hops=next_hops,
                     dev_connected=dev_connected,
                     ids_available=ids_available
                     )

            int_list.append(d)
        return int_list

    def get_node_info_dict(self):
        try:
            return {self.get_node_name(): {'ip_address': self.hostname,
                                           'interfaces': self.get_node_interfaces_up()}
                    }
        except exceptions.EasySNMPTimeoutError:
            return None

    def _get_devs_connected(self, int_index, names_list, ints_list):
        node_name = next((x[0] for x in names_list if x[1] == int_index), None)
        int_name = next((x[0] for x in ints_list if x[1] == int_index), None)
        if node_name and int_name:
            return node_name, int_name
        else:
            return None

    def _get_trunk_ids_available(self, trunks_map_bin, vlan_ints_list):

        bin_list = ["{0:04b}".format(int(x, 16)) for x in binascii.b2a_hex(trunks_map_bin)]
        bin_str = ''.join(bin_list)
        vlan_ints_name_list = [x.value for x in vlan_ints_list]
        avail_list = [index for index, value in enumerate(bin_str) if value == '0' and
                      index != 0 and 'Vlan'+str(index) not in vlan_ints_name_list]
        return utils.stretch_ids(avail_list)


if __name__ == '__main__':
    obj = SnmpCisco()
    obj.connect('192.168.2.1', community='public', version=2)
    print obj.get_node_info_dict()
