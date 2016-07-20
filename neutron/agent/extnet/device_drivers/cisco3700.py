import re
import itertools
from extnet_networkcontroller.device_drivers import driver_api
from extnet_networkcontroller.common import const

import pexpect

# Variable to use when the expected result from the command line is a prompt ready to enter commands.
COMMAND_PROMPT = '[#$>]'


class Cisco3700(driver_api.ExtNetDeviceDriverBase):

    def _get_node_id(self, available_list):
        # [(123, 130), (1000, 2000)]
        l = [[int(ids.split(':')[0]), int(ids.split(':')[1])]
             if len(ids.split(':')) > 1 else [int(ids)] for ids in available_list.split(',')]

        num_list = list()
        for item in l:
            if len(item) > 1:
                num_list += range(item[0], item[1] + 1)
            else:
                num_list += item

        num_list.sort()

        new_id = num_list.pop(0)

        l2 = [':'.join([str(t[0][1]), str(t[-1][1])]) if t[0][1] - t[-1][1] != 0 else str(t[0][1]) for t in
              (tuple(g[1]) for g in itertools.groupby(enumerate(num_list), lambda (i, x): i - x))]

        available_list = ','.join(l2)

        return new_id, available_list

    def _get_allowed_vlans_on_interface(self, interface):
        self._exit_config_mode()

        # print 'sh int %s tr' % interface
        res = self._send_command('sh int %s tr' % interface)

        vlans_allowed = re.split('\s+', res.split('\n')[6])[1]

        self._enter_config_mode()

        return vlans_allowed

    def _get_new_bridge_group(self, vnetwork):
        bridge_group = self.dev_config_dict.get('bridge_groups_attributed').get(vnetwork)
        if bridge_group:
            return bridge_group
        else:
            new_bg, avail_list = self._get_node_id(self.dev_config_dict.get('bridge_groups_available'))
            self.dev_config_dict['bridge_groups_attributed'][vnetwork] = new_bg
            self.dev_config_dict['bridge_groups_available'] = avail_list
            self.save_device_configs()
            return new_bg

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
            print "ERROR connecting to %s using telnet." % self.device_name
            print e
            return None

    def _enter_config_mode(self):
        self._send_command('configure terminal')

    def _exit_config_mode(self):
        self.spawn.sendline('end')
        self.spawn.expect(COMMAND_PROMPT)

    def _close_telnet_session(self):
        self._send_command('write')
        self.spawn.sendline('exit')

    def _send_command(self, command):
        self.spawn.sendline(command)
        self.spawn.expect(COMMAND_PROMPT)
        return self.spawn.before

    def deploy_port(self, interface_type, interface_name, link_segmentation_id, **kwargs):
        self._init_telnet_session()
        self._enter_config_mode()

        self._send_command('interface %s' % interface_name)

        self._send_command('no ip address')

        if interface_type == const.L3:

            bridge_group = self._get_bridge_group(kwargs.get('vnetwork'))

            self._send_command('bridge-group %s' % bridge_group)

            msg = const.OK

        # self.spawn.sendline('bridge-group %s' % bridge_group)
        # r = self.spawn.expect(['does not support bridging', COMMAND_PROMPT])

        elif interface_type == const.L2 and link_segmentation_id:

            self._send_command('switchport mode access')

            self._send_command('switchport access vlan %s' % link_segmentation_id)

            msg = const.OK

        else:

            msg = "ERROR - Interface type not supported." \
                  % interface_name

        self._exit_config_mode()
        self._close_telnet_session()

        return msg

    def undeploy_port(self, port):
        pass

    def driver_name(self):
        return "Cisco 3700"

    def driver_overlay_types(self):
        return ['vlan', 'gre']

    def delete_port(self, port):
        self._close_telnet_session()

    def driver_protocol(self):
        return 'telnet'

    def undeploy_link(self,
                      link_type,
                      interface_name,
                      segmentation_id,
                      **kwargs):

        self._init_telnet_session()
        self._enter_config_mode()

        if link_type == const.GRE:

            self._send_command('no interface Tunnel%s' % segmentation_id)

        elif link_type == const.VLAN:

            self._exit_config_mode()

            self._send_command('vlan database')

            self._send_command('no vlan %s' % segmentation_id)

            self._send_command('exit')

            self._enter_config_mode()

            self._send_command('no interface vlan %s' % segmentation_id)

            self._send_command('interface %s' % interface_name)

            self._send_command('switchport trunk allowed vlan remove %s' % segmentation_id)

        else:
            print 'Here!'
            return "ERROR - Link type not supported by the driver %s" % self.driver_name()

        self._exit_config_mode()
        self._close_telnet_session()
        return const.OK

    def deploy_link(self,
                    link_type,
                    interface_name,
                    tun_destination,
                    segmentation_id,
                    **kwargs):

        bridge_group = self._get_new_bridge_group(kwargs.get('vnetwork'))

        self._init_telnet_session()
        self._enter_config_mode()

        self._send_command('bridge irb')

        self._send_command('bridge %s protocol ieee' % bridge_group)

        if link_type == const.GRE:

            self._send_command('interface Tunnel%s' % segmentation_id)

            self._send_command('tunnel key %s' % segmentation_id)

            self._send_command('no ip address')

            self._send_command('tunnel source %s' % interface_name)

            if tun_destination is not None:
                self._send_command('tunnel destination %s' % tun_destination)
            else:
                return "ERROR - Error creating the link on %s. Missing tunnel destination." % self.device_name

            self._send_command('bridge-group %s' % bridge_group)

            self._send_command('bridge-group %s spanning-disabled' % bridge_group)

        elif link_type == const.VLAN:

            vlans_allowed = self._get_allowed_vlans_on_interface(interface_name)
            if vlans_allowed == '1-4094' or vlans_allowed == '1-4095':
                vlans_allowed = str(segmentation_id) + ',1,1002-1005'
            elif str(segmentation_id) not in vlans_allowed.split(','):
                vlans_allowed = str(segmentation_id) + ',' + vlans_allowed

            self._send_command('va %s' % segmentation_id)

            self._send_command('interface vlan %s' % segmentation_id)

            self._send_command('bridge-group %s' % bridge_group)

            self._send_command('interface %s' % interface_name)

            self._send_command('no ip address')

            self._send_command('switchport mode trunk')

            self._send_command('switchport trunk allowed vlan ' + vlans_allowed)

        else:
            return "ERROR - Link type not supported by the driver %s" % self.driver_name()

        self._exit_config_mode()
        self._close_telnet_session()
        return const.OK

    def __init__(self, device_name, ip_address, dev_config_location):
        super(Cisco3700, self).__init__(device_name, ip_address, dev_config_location)
        self.password = self.dev_config_dict.get('password')
        self.port = self.dev_config_dict.get('port')
