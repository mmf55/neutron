import re
from easysnmp import Session
from easysnmp import exceptions

import topology_discovery_api


OID_NODE_NAME = 'iso.3.6.1.2.1.1.5.0.'
OID_NODE_IFDESCR = 'iso.3.6.1.2.1.2.2.1.2.'
OID_NODE_IFOPERSTATUS = 'iso.3.6.1.2.1.2.2.1.8.'
OID_NODE_IPADDRESS = 'iso.3.6.1.2.1.4.20.1.2.'
OID_NODE_NEXTHOPS = 'iso.3.6.1.2.1.4.22.1.3.'


class SnmpCisco(topology_discovery_api.TopoDiscMechanismApi):

    def connect(self, hostname, **kwargs):
        self.hostname = hostname
        self.session = Session(hostname=hostname,
                               community=kwargs['community'],
                               version=kwargs['version'])

    def get_node_name(self):
        return self.session.get(OID_NODE_NAME).value

    def get_node_interfaces_up(self):
        int_list = []
        p1 = re.compile("^FastEthernet")
        p2 = re.compile("^Vlan")
        fe_ints_list = [x for x in self.session.walk(OID_NODE_IFDESCR)
                        if (p1.match(x.value) or p2.match(x.value)) and
                        self.session.get(OID_NODE_IFOPERSTATUS+x.oid.split(OID_NODE_IFDESCR)[1]).value == '1']

        ips_list = [(x.value, x.oid.split(OID_NODE_IPADDRESS)[1]) for x in self.session.walk(OID_NODE_IPADDRESS)]
        # print ips_list
        for interface in fe_ints_list:
            # print interface
            ip_address = next((x[1] for x in ips_list if x[0] == interface.oid.split(OID_NODE_IFDESCR)[1]), None)
            # print ip_address
            next_hops = [x.value for x in self.session.walk(OID_NODE_NEXTHOPS+interface.oid.split(OID_NODE_IFDESCR)[1])
                         if ip_address != x.value]
            # print next_hops
            d = dict(name=interface.value,
                     ip_address=ip_address,
                     next_hops=next_hops)
            int_list.append(d)
        return int_list

    def get_node_info_dict(self):
        try:
            return {self.get_node_name(): {'ip_address': self.hostname,
                                           'interfaces': self.get_node_interfaces_up()}
                    }
        except exceptions.EasySNMPTimeoutError:
            return None

if __name__ == '__main__':
    obj = SnmpCisco()
    obj.connect('192.168.2.1', community='public', version=2)
    print obj.get_node_info_dict()
