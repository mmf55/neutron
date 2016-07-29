import re

import pexpect
from easysnmp import Session
from easysnmp import exceptions

from extnet_networkcontroller.topology_discovery import topology_discovery_api


OID_NODE_NAME = 'iso.3.6.1.2.1.1.5.0.'
OID_NODE_IFDESCR = 'iso.3.6.1.2.1.2.2.1.2.'
OID_NODE_IFOPERSTATUS = 'iso.3.6.1.2.1.2.2.1.8.'
OID_NODE_IPADDRESS = 'iso.3.6.1.2.1.4.20.1.2.'
OID_NODE_NETMASKS = 'iso.3.6.1.2.1.4.20.1.3.'
OID_NODE_NEXTHOPS = 'iso.3.6.1.2.1.4.22.1.3.'


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
        fe_ints_list = [x for x in self.session.walk(OID_NODE_IFDESCR)
                        if (p1.match(x.value) or p2.match(x.value)) and
                        self.session.get(OID_NODE_IFOPERSTATUS+x.oid_index).value == '1']

        ips_list = [(x.value, x.oid_index) for x in self.session.walk(OID_NODE_IPADDRESS)]
        netmasks_list = [(x.value, x.oid_index) for x in self.session.walk(OID_NODE_NETMASKS)]
        # print ips_list
        for interface in fe_ints_list:
            # print interface
            ip_address = next((x[1] for x in ips_list if x[0] == interface.oid_index), None)
            netmask = next((x[0] for x in netmasks_list if x[1] == ip_address), None)
            # print ip_address
            next_hops = [x.value for x in self.session.walk(OID_NODE_NEXTHOPS+interface.oid_index)
                         if ip_address != x.value]
            # print next_hops
            d = dict(name=interface.value,
                     ip_address=ip_address,
                     netmask=netmask,
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


# Variable to use when the expected result from the command line is a prompt ready to enter commands.
COMMAND_PROMPT = '[#$>]'
PORT = 23
PASSWORD = 'pass'


class BashCisco(object):

    def __init__(self, interface_name, ip_address, port, password):
        self.interface_name = interface_name
        self.ip_address = ip_address
        self.port = port
        self.password = password

    def _send_command(self, command):
        self.spawn.sendline(command)
        self.spawn.expect(COMMAND_PROMPT)
        return self.spawn.before

    def _init_telnet_session(self):
        try:
            self.spawn = pexpect.spawn('telnet %s %s' % (self.ip_address, self.port))
            self.spawn.expect('Password:')
            self.spawn.sendline(self.password)
            self.spawn.expect(COMMAND_PROMPT)

            self.spawn.sendline('enable')
            self.spawn.expect(['Password:', COMMAND_PROMPT])
            self._send_command(self.password)

        except pexpect.ExceptionPexpect as e:
            print "ERROR connecting to %s using telnet." % self.ip_address
            print e
            return None

    def get_interface_trunks(self):
        self._init_telnet_session()

        trunking_info = self._send_command('sh int trunk')

        trunking_info = re.sub("\\r", '', trunking_info)

        trunking_info = trunking_info.split('\n')

        trunking_info = trunking_info[6].split('     ')

        res1 = None
        m1 = re.search("\d\/\d", trunking_info[0])
        if m1:
            res1 = m1.group(0)

        res2 = None
        m2 = re.search("\d\/\d", trunking_info[0])
        if m2:
            res2 = m2.group(0)

        if res1 and res2:
            if res1 == res2:
                return trunking_info[1]

        return None


# if __name__ == '__main__':
#     obj = SnmpCisco()
#     obj.connect('192.168.2.1', community='public', version=2)
#     print obj.get_node_info_dict()

if __name__ == '__main__':
    bc = BashCisco('192.168.2.1', PORT, PASSWORD)
    print bc.get_interface_trunks()
