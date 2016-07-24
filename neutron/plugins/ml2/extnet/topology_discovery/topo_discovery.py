import snmp

import topology_discovery_api


class TopologyDiscovery(snmp.SnmpCisco,
                        topology_discovery_api.TopologyDicoveryApi):

    def __init__(self):
        self.dev_dict = {}

    def get_devices_info(self, ip_address, **kwargs):
        self.connect(ip_address, community='public', version=2)
        node_info = self.get_node_info_dict()
        if node_info:
            node, node_dict = node_info.items()[0]
            if not self._host_already_checked(node):
                self.dev_dict[node_info.keys()[0]] = node_info.values()[0]
                for interface in node_dict['interfaces']:
                    n_hops_list = interface['next_hops']
                    if n_hops_list:
                        for ip_address in n_hops_list:
                            # print ip_address
                            node_dict = self.get_devices_info(ip_address)
                            if node_dict:
                                node_info[node_dict.keys()[0]] = node_dict.values()[0]
                return node_info

        return None

            # self.dev_list.append()

    def _host_already_checked(self, node_to_check):
        return next((x for x in self.dev_dict.items() if x[0] == node_to_check), None)
        for node, node_info in self.dev_dict.items():
            interfaces_list = node_info['interfaces']
            return next((x for x in interfaces_list
                         if x['ip_address'] == ip_address), None)


if __name__ == '__main__':
    td = TopologyDiscovery()
    print td.get_devices_info('192.168.2.1')
