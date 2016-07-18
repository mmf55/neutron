import snmp

import topology_discovery_api


class TopologyDiscovery(snmp.SnmpCisco,
                        topology_discovery_api.TopologyDicoveryApi):

    def __init__(self):
        self.dev_list = []

    def get_devices_info(self, ip_address, **kwargs):
        if not self._host_already_checked(ip_address):
            self.connect(ip_address, community='public', version=2)
            node_ints = self.get_node_info_dict()
            if node_ints:
                self.dev_list += [node_ints]
                node, node_dict = node_ints.items()[0]
                node_ints = [node_ints]
                for interface in node_dict['interfaces']:
                    n_hops_list = interface['next_hops']
                    if n_hops_list:
                        for ip_address in n_hops_list:
                            # print ip_address
                            node_ints += self.get_devices_info(ip_address)
                return node_ints

        return []

            # self.dev_list.append()

    def _host_already_checked(self, ip_address):
        for node_dict in self.dev_list:
            interfaces_list = node_dict.items()[0][1]['interfaces']
            return next((x for x in interfaces_list
                         if x['ip_address'] == ip_address), None)


if __name__ == '__main__':
    td = TopologyDiscovery()
    print td.get_devices_info('192.168.2.1')
