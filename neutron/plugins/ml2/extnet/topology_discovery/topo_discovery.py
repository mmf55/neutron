import snmp

import topology_discovery_api


class TopologyDiscovery(snmp.SnmpCisco,
                        topology_discovery_api.TopologyDicoveryApi):

    def __init__(self):
        self.nodes_info = {}
        self.visited_nodes = []

    def get_devices_info(self, ip_address, **kwargs):
            self.connect(ip_address, community='public', version=2)
            node_info = self.get_node_info_dict()
            if node_info:
                node, node_dict = node_info.items()[0]
                self.nodes_info[node] = node_dict
                for interface in node_dict['interfaces']:
                    n_hops_list = interface['next_hops']
                    if n_hops_list:
                        for ip_address in n_hops_list:
                            # print ip_address
                            self.connect(ip_address, community='public', version=2)
                            node_name = self.get_node_name()
                            if node_name and node_name not in self.nodes_info.keys():
                                self.get_devices_info(ip_address)
            return self.nodes_info

    def _host_already_checked(self, next_node):
        return next_node in self.dev_list


if __name__ == '__main__':
    td = TopologyDiscovery()
    print td.get_devices_info('192.168.2.1')
