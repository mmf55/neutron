import itertools
import re
import oslo_messaging
from oslo_config import cfg
from oslo_log import log as logging

from neutron.common import topics
from neutron.common import rpc as n_rpc

from neutron.callbacks import registry, resources, events

from neutron.plugins.ml2.common import extnet_exceptions
from neutron.plugins.ml2.extnet import config
from extnet_networkcontroller.topology_discovery import topo_discovery
from neutron.plugins.ml2.extnet.topology_discovery import snmp_bash
from neutron.plugins.ml2.extnet.network_mapper import extnet_nm

from neutron.db import extnet_db_mixin
from neutron.db import extnet_db as models

from extnet_networkcontroller.network_controller import net_ctrl
from extnet_networkcontroller.network_controller import dev_ctrl_mgr
from extnet_networkcontroller.device_controller import dev_ctrl
from extnet_networkcontroller.common import const
from extnet_networkcontroller.common import utils

from sqlalchemy import or_

LOG = logging.getLogger(__name__)


# This class holds the main logic for extending the virtual networks to the campus network.
class ExtNetControllerMixin(extnet_db_mixin.ExtNetworkDBMixin,
                            net_ctrl.ExtNetController):
    def initialize_extnetcontroller(self):

        config_dict = {device_ctrl: dev_name_list.split(';')
                       for device_ctrl, dev_name_list in cfg.CONF.EXTNET_CONTROLLER.device_controllers.items()}

        device_ctrl_mgr = ExtNetDeviceCtrlManager(config_dict)

        nm = extnet_nm.ExtNetNetworkMapperSP()
        super(ExtNetControllerMixin, self).__init__(device_ctrl_mgr, mapper=nm)

    def create_extlink(self, context, extlink):

        # Get the necessary info
        link = extlink['extlink']
        interface1 = self.get_extinterface(context, link.get('extinterface1_id'))
        interface2 = self.get_extinterface(context, link.get('extinterface2_id'))

        node1 = self.get_extnode(context, interface1.get('extnode_id'))
        node2 = self.get_extnode(context, interface2.get('extnode_id'))

        segment = self.get_extsegment(context, interface1.get('extsegment_id'))

        if self._extinterface_has_extports(context, interface1.get('id')) \
                or self._extinterface_has_extports(context, interface2.get('id')):
            raise extnet_exceptions.ExtInterfaceHasPortsInUse()

        if interface1.get('extsegment_id') != interface2.get('extsegment_id'):
            raise extnet_exceptions.ExtInterfacesNotInSameSegment()

        if (segment.get('type_supported') == const.GRE and not (interface1.get('type') == 'l3' and
                                                                        interface2.get('type') == 'l3')) or \
                (segment.get('type_supported') == const.VLAN and not (interface1.get('type') == 'l2' and
                                                                              interface2.get('type') == 'l2')):
            raise extnet_exceptions.ExtLinkTypeNotSupportedByInterfaces()

        link['segmentation_id'] = self._get_segmentation_id(context,
                                                            segment.get('id'),
                                                            segment.get('type_supported'),
                                                            link.get('network_id'))

        # Call create link to make the changes on the network.
        if self.deploy_link(link,
                            segment.get('type_supported'),
                            interface1,
                            interface2,
                            node1,
                            node2,
                            vnetwork=link.get('network_id'),
                            context=context) != const.OK:
            raise extnet_exceptions.ExtLinkErrorApplyingConfigs()

        # Save new link on the database
        return super(ExtNetControllerMixin, self).create_extlink(context, extlink)

    def delete_extlink(self, context, id):
        link = self.get_extlink(context, id)

        interface1 = self.get_extinterface(context, link.get('extinterface1_id'))
        interface2 = self.get_extinterface(context, link.get('extinterface2_id'))

        node1 = self.get_extnode(context, interface1.get('extnode_id'))
        node2 = self.get_extnode(context, interface2.get('extnode_id'))

        segment = self.get_extsegment(context, interface1.get('extsegment_id'))

        if self.undeploy_link(link,
                              segment.get('type_supported'),
                              interface1,
                              interface2,
                              node1,
                              node2,
                              vnetwork=link.get('network_id'),
                              context=context) != const.OK:
            raise extnet_exceptions.ExtLinkErrorApplyingConfigs()

        if self._set_segmentation_id(context,
                                     link.get('segmentation_id'),
                                     segment.get('id'),
                                     segment.get('type_supported'),
                                     link.get('network_id')) != const.OK:
            raise extnet_exceptions.ExtLinkErrorInSetSegID()

        return super(ExtNetControllerMixin, self).delete_extlink(context, id)

    def create_extport(self, context, port):

        self.setup_controller_host(context)

        node = self.get_extnode_by_name(context, port.get('extnode_name'))

        if not node:
            self.discover_topology(context)

        node = self.get_extnode_by_name(context, port.get('extnode_name'))

        if not node:
            raise extnet_exceptions.ExtNodeNotFound()

        if port.get('extinterface_name'):
            interface = self.get_extinterface_by_name(context,
                                                      port.get('extinterface_name'),
                                                      node.get('id'))

            if not interface:
                self.discover_topology(context)

            interface = self.get_extinterface_by_name(context,
                                                      port.get('extinterface_name'),
                                                      node.get('id'))

            if not interface:
                raise extnet_exceptions.ExtInterfaceNotFound()

            if self._extinterface_has_extlinks(context, interface.get('id')):
                raise extnet_exceptions.ExtPortErrorApplyingConfigs()

        else:
            interface = None
            interfaces = self._get_extnode_interfaces(context, node.get('id'))
            if interfaces:
                interface = next((x for x in interfaces if not self._extinterface_has_extlinks(context, x.get('id'))),
                                 None)
            if not interface:
                raise extnet_exceptions.NoExtInterfacesAvailable()

        segmentation_id = None

        interface_extports = self._extinterface_has_extports(context, interface.get('id'))
        if interface_extports:
            port_on_db = self.get_port(context, interface_extports[0].id)
            if port_on_db.get('network_id') != port.get('network_id'):
                raise extnet_exceptions.ExtPortErrorApplyingConfigs()

        links = self._get_all_links_on_extnode(context,
                                               node.get('id'),
                                               port.get('network_id'))
        if links:
            if interface.get('type') == 'l2':
                node_interfaces = self._get_extnode_interfaces_with_interface(context, interface.get('id'), 'l2')
                node_interfaces = [x.id for x in node_interfaces]
                segmentation_id = next((x.segmentation_id for x in links
                                        if (x.extinterface1_id in node_interfaces or
                                            x.extinterface2_id in node_interfaces)), None)
                if not segmentation_id:
                    raise extnet_exceptions.ExtLinkSegmentationIdNotAvailable()
                else:
                    self.set_seg_id_extport(context, port.get('id'), segmentation_id)
        else:

            # Build network graph
            net_graph = self._build_net_graph(context)

            LOG.debug(net_graph)
            # Apply links to the best path found.
            first_node = self.get_extnode_by_name(context, cfg.CONF.EXTNET_CONTROLLER.net_ctrl_node_name)

            path = self.build_virtual_network_path(graph=net_graph,
                                                   start=first_node.id,
                                                   end=node.get('id'))
            LOG.debug(path)
            if not path:
                raise extnet_exceptions.ExtNodeHasNoLinks()

            if self._apply_virtual_network_path(context, port, path) != const.OK:
                raise extnet_exceptions.ExtNodeHasNoLinks()

            if len(interface_extports) == 1:
                LOG.debug(interface)
                if self.deploy_port(interface,
                                    node,
                                    segmentation_id,
                                    vnetwork=port.get('network_id'),
                                    context=context) != const.OK:
                    raise extnet_exceptions.ExtPortErrorApplyingConfigs()

    def delete_extport(self, context, port):
        port_id = port.get('id')
        ext_port = self.get_extport(context, port_id)

        if ext_port:
            interface = self.get_extinterface(context, ext_port.get('extinterface_id'))
            node = self.get_extnode(context, interface.get('extnode_id'))

            interface_extports = self._extinterface_has_extports(context, interface.get('id'))
            extport_db = context.session.query(models.ExtPort).filter_by(id=port_id)
            for link in extport_db.extlinks:
                if len(link.extports) == 1:
                    self.delete_extlink(context, link.id)

            if len(interface_extports) == 1:
                if self.undeploy_port(interface,
                                      node,
                                      ext_port.get('segmentation_id'),
                                      vnetwork=port.get('network_id'),
                                      context=context) != const.OK:
                    raise extnet_exceptions.ExtPortErrorApplyingConfigs()

    # ------------------------------------ Auxiliary functions ---------------------------------------

    def discover_topology(self, context):
        td = topo_discovery.TopologyDiscovery(snmp_bash.SnmpCisco())
        topo_dict = td.get_devices_info(cfg.CONF.EXTNET_CONTROLLER.device_controllers.next_hop_ip)

        LOG.debug(topo_dict)

        if not topo_dict:
            raise extnet_exceptions.ExtNodeErrorOnTopologyDiscover()

        for node, node_info_dict in topo_dict.items():

            existing_node = self.get_extnode_by_name(context, node)
            if not existing_node:
                node_dict = dict(name=node,
                                 ip_address=node_info_dict.get('ip_address'))
                node_dict = {'extnode': node_dict}
                node_created = super(ExtNetControllerMixin, self).create_extnode(context, node_dict)
                node_id = node_created.get('id')
            else:
                node_id = existing_node.id

            node_interfaces_list = node_info_dict.get('interfaces')
            for interface in node_interfaces_list:
                interface_exists = None
                if existing_node:
                    interfaces = existing_node.extinterfaces
                    interface_exists = next((x for x in interfaces if x.name == interface.get('name')), None)
                if not existing_node or not interface_exists:
                    p = re.compile("^FastEthernet")
                    if p.match(interface.get('name')):
                        if interface.get('ip_address') is not None:
                            net_type = 'l3'
                        else:
                            net_type = 'l2'

                        # handle the external segment creation or get.
                        extsegment_id = interface.get('extsegment_id')

                        if not extsegment_id:
                            extsegment_id = self._handle_extsegment(context,
                                                                    node,
                                                                    interface,
                                                                    topo_dict)

                        interface_dict = dict(name=interface.get('name'),
                                              ip_address=interface.get('ip_address'),
                                              type=net_type,
                                              extnode_id=node_id,
                                              extsegment_id=extsegment_id
                                              )
                        interface_dict = {'extinterface': interface_dict}
                        interface_created = super(ExtNetControllerMixin, self).create_extinterface(context,
                                                                                                   interface_dict)

    def setup_controller_host(self, context):
        if not self.get_extnode_by_name(context, 'OVS'):
            node_dict = dict(name='OVS')
            node_dict = {'extnode': node_dict}
            ovs_node = super(ExtNetControllerMixin, self).create_extnode(context, node_dict)

            ovs_interface = dict(name='e1',
                                 ip_address='192.168.2.2',
                                 netmask='255.255.255.0',
                                 next_hops='192.168.2.1',
                                 dev_connected=None,
                                 ids_available=None
                                 )

            extsegment_id = self._handle_extsegment(context,
                                                    ovs_node.get('name'),
                                                    ovs_interface,
                                                    )

            interface_dict = dict(name=ovs_interface.get('name'),
                                  ip_address=ovs_interface.get('ip_address'),
                                  type=const.L3 if ovs_interface.get('ip_address') else const.L2,
                                  extnode_id=ovs_node.get('id'),
                                  extsegment_id=extsegment_id
                                  )
            interface_dict = {'extinterface': interface_dict}

            ovs_interface = super(ExtNetControllerMixin, self).create_extinterface(context,
                                                                                   interface_dict)

    def _apply_virtual_network_path(self, context, port, path):
        port_id = port.get('id')
        network_id = port.get('network_id')
        i = 0
        extsegments = context.session.query(models.ExtSegment).all()
        while i + 1 != len(path):
            node1 = context.session.query(models.ExtNode).filter_by(id=path[i]).first()
            node2 = context.session.query(models.ExtNode).filter_by(id=path[i + 1]).first()
            for extsegment in extsegments:
                if bool(set(node1.extinterfaces) & set(extsegment.extinterfaces)) and \
                        bool(set(node2.extinterfaces) & set(extsegment.extinterfaces)):
                    links_on_db = self._get_all_links_on_extsegment(context, extsegment.id, network_id)
                    if links_on_db:
                        link_on_db = links_on_db[0]
                        link_on_db.extports.append(port_id)
                    else:
                        extlink = dict(name='link' + node1.name + node2.name,
                                       extinterface1_id=extsegment.extinterfaces[0].id,
                                       extinterface2_id=extsegment.extinterfaces[1].id,
                                       network_id=network_id,
                                       extport=port_id
                                       )
                        extlink = {'extlink': extlink}
                        LOG.debug(extlink)
                        self.create_extlink(context, extlink)
            i += 1
        return const.OK

    def _build_net_graph(self, context):
        all_nodes = context.session.query(models.ExtNode).all()
        graph = {}
        for node in all_nodes:
            nodes_conn_list = []
            for interface in node.extinterfaces:
                if interface.extsegment:
                    neigh_interface = next((x for x in interface.extsegment.extinterfaces if x != interface), None)
                    if neigh_interface:
                        nodes_conn_list.append(neigh_interface.extnode.id)
            graph[node.id] = nodes_conn_list
        return graph

    def _handle_extsegment(self, context, node_name, interface, topo_dict=None):

        ip_address = interface.get('ip_address')
        if ip_address:
            # l3
            netmask = interface.get('netmask')
            subnet = self._get_extnet_subnet(ip_address, netmask)

            extsegment_name = 'l3' + re.sub('[.]', '', subnet)

            extsegment_in_db = self.get_extsegment_by_name(context, extsegment_name)

            if not extsegment_in_db:

                extsegment_dict = dict(name=extsegment_name,
                                       type_supported=const.GRE,
                                       ids_available='0:10'
                                       )

                extsegment_dict = {'extsegment': extsegment_dict}
                extsegment_db_dict = super(ExtNetControllerMixin, self).create_extsegment(context,
                                                                                          extsegment_dict)
                return extsegment_db_dict['id']
            else:
                return extsegment_in_db.get('id')
        else:
            # l2
            dev_connected = interface.get('dev_connected')

            if dev_connected and topo_dict and topo_dict.get(dev_connected[0]):

                extsegment_name = 'l2' + node_name + dev_connected[0]

                extsegment_in_db = self.get_extsegment_by_name(context, extsegment_name)

                if not extsegment_in_db:

                    interface_conn = topo_dict[dev_connected[0]]['interfaces']
                    interface_next = next((x for x in interface_conn if x.get('name') == dev_connected[1]))

                    va_interface = interface['ids_available']
                    va_interface_next = interface_next['ids_available']

                    ids_avail_list = list(
                        set(utils.shrink_ids(va_interface)).intersection(utils.shrink_ids(va_interface_next)))
                    ids_avail_str = utils.stretch_ids(ids_avail_list)

                    extsegment_dict = dict(name=extsegment_name,
                                           type_supported=const.VLAN,
                                           ids_available=ids_avail_str
                                           )

                    extsegment_dict = {'extsegment': extsegment_dict}
                    extsegment_db_dict = super(ExtNetControllerMixin, self).create_extsegment(context,
                                                                                              extsegment_dict)

                    interface_next['extsegment_id'] = extsegment_db_dict['id']

                else:
                    return extsegment_in_db.get('id')

                return extsegment_db_dict['id']
            else:
                return None

    def _get_extnet_subnet(self, ip_address, netmask):
        l_netmask = [int(x) for x in netmask.split('.')]
        l_ip = [int(x) for x in ip_address.split('.')]
        subnet = map(lambda x, y: x & y, l_netmask, l_ip)
        subnet = [str(x) for x in subnet]
        return '.'.join(subnet)

    def _get_extnode_interfaces(self, context, node_id):
        node_interfaces = context.session.query(models.ExtNode).filter_by(id=node_id).first().extinterfaces
        node_interfaces_list = []
        for interface in node_interfaces:
            node_interfaces_list.append(self._make_extinterface_dict(interface))
        return node_interfaces_list

    def _get_extnode_interfaces_with_interface(self, context, interface_id, type=None):
        if type:
            interface = context.session.query(models.ExtInterface) \
                .filter_by(id=interface_id) \
                .filter_by(type=type) \
                .first()
        else:
            interface = context.session.query(models.ExtInterface).filter_by(id=interface_id).first()

        return interface.extnode.extinterfaces

    def _extinterface_has_extports(self, context, interface_id):
        interface = context.session.query(models.ExtInterface).filter_by(id=interface_id).first()
        return interface.extports

    def _get_all_links_on_extnode(self, context, extnode_id, network_id):
        node = context.session.query(models.ExtNode).filter_by(id=extnode_id).first()
        links = []
        for interface in node.extinterfaces:
            links += context.session.query(models.ExtLink) \
                .filter(or_(models.ExtLink.extinterface1_id == interface.id,
                            models.ExtLink.extinterface2_id == interface.id)) \
                .filter(models.ExtLink.network_id == network_id) \
                .all()
            links = list(set(links))
        return links

    def _get_all_links_on_extsegment(self, context, segment_id, network_id):
        interfaces = context.session.query(models.ExtInterface).filter_by(extsegment_id=segment_id).all()
        links = []
        for interface in interfaces:
            links += context.session.query(models.ExtLink) \
                .filter(or_(models.ExtLink.extinterface1_id == interface.id,
                            models.ExtLink.extinterface2_id == interface.id)) \
                .filter(models.ExtLink.network_id == network_id) \
                .all()
            links = list(set(links))
        return links

    def _get_segmentation_id(self, context, segment_id, conn_type, network_id):
        segment = context.session.query(models.ExtSegment).filter_by(id=segment_id).first()

        if conn_type == const.VLAN:
            links = self._get_all_links_on_extsegment(context, segment_id, network_id)
            if links:
                return links[0].segmentation_id

        ids_avail = segment.ids_available

        if not ids_avail:
            raise extnet_exceptions.ExtLinkErrorObtainingSegmentationID()

        num_list = utils.shrink_ids(ids_avail)

        num_list.sort()

        seg_id = num_list.pop(0)

        segment.ids_available = utils.stretch_ids(num_list)

        return seg_id

    def _set_segmentation_id(self, context, id_to_set, segment_id, conn_type, network_id):

        segment = context.session.query(models.ExtSegment).filter_by(id=segment_id).first()

        if conn_type == const.VLAN:
            links = self._get_all_links_on_extsegment(context, segment_id, network_id)
            links = {x for x in links if x['segmentation_id'] != id_to_set}
            if links:
                return const.OK

        ids_avail = segment.ids_available

        num_list = utils.shrink_ids(ids_avail)

        num_list.append(int(id_to_set))
        num_list.sort()

        segment.ids_available = utils.stretch_ids(num_list)

        return const.OK


# Controls the deploy requests by directing themselves to the correspondent device controller
class ExtNetDeviceCtrlManager(dev_ctrl_mgr.ExtNetDeviceControllerManager):
    def __init__(self, config):
        super(ExtNetDeviceCtrlManager, self).__init__(config)

    def deploy_link_on_node(self, interface, node, network_type, segmentation_id, **kwargs):
        context = kwargs.get('context')
        node_name = node['name']
        topic = self.get_device_controller(node_name)

        topic_create_extlink = topics.get_topic_name(topic,
                                                     topics.EXTNET_LINK,
                                                     topics.CREATE)
        target = oslo_messaging.Target(topic=topic, version='1.0')
        client = n_rpc.get_client(target)
        cctxt = client.prepare(topic=topic_create_extlink,
                               fanout=False,
                               timeout=30)
        return cctxt.call(context,
                          'deploy_link',
                          node=node,
                          segmentation_id=segmentation_id,
                          network_type=network_type,
                          interface=interface,
                          vnetwork=kwargs.get('vnetwork'),
                          remote_ip=kwargs.get('remote_ip'))

    def undeploy_link_on_node(self, interface, node, network_type, segmentation_id, **kwargs):
        context = kwargs.get('context')
        node_name = node['name']
        topic = self.get_device_controller(node_name)

        topic_create_extlink = topics.get_topic_name(topic,
                                                     topics.EXTNET_LINK,
                                                     topics.DELETE)
        target = oslo_messaging.Target(topic=topic, version='1.0')
        client = n_rpc.get_client(target)
        cctxt = client.prepare(topic=topic_create_extlink,
                               fanout=False,
                               timeout=30)
        return cctxt.call(context,
                          'undeploy_link',
                          node=node,
                          segmentation_id=segmentation_id,
                          interface=interface,
                          network_type=network_type,
                          vnetwork=kwargs.get('vnetwork'),
                          remote_ip=kwargs.get('remote_ip'))

    def deploy_port_on_node(self, interface, node, segmentation_id, **kwargs):
        context = kwargs.get('context')
        node_name = node['name']
        topic = self.get_device_controller(node_name)
        topic_create_extport = topics.get_topic_name(topic,
                                                     topics.EXTNET_PORT,
                                                     topics.CREATE)
        target = oslo_messaging.Target(topic=topic, version='1.0')
        client = n_rpc.get_client(target)
        cctxt = client.prepare(topic=topic_create_extport,
                               fanout=False,
                               timeout=30)

        return cctxt.call(context,
                          'deploy_port',
                          segmentation_id=segmentation_id,
                          node=node,
                          interface=interface,
                          vnetwork=kwargs.get('vnetwork'))

    def undeploy_port_on_node(self, interface, node, segmentation_id, **kwargs):
        context = kwargs.get('context')
        node_name = node['name']
        topic = self.get_device_controller(node_name)
        topic_create_extport = topics.get_topic_name(topic,
                                                     topics.EXTNET_PORT,
                                                     topics.DELETE)
        target = oslo_messaging.Target(topic=topic, version='1.0')
        client = n_rpc.get_client(target)
        cctxt = client.prepare(topic=topic_create_extport,
                               fanout=False,
                               timeout=30)

        return cctxt.call(context,
                          'undeploy_port',
                          segmentation_id=segmentation_id,
                          node=node,
                          interface=interface,
                          vnetwork=kwargs.get('vnetwork'))


# This turns the OVS agent to a device controller.
class ExtNetOVSAgentMixin(dev_ctrl.ExtNetDeviceController):
    def deploy_link(self, ctxt, interface, node, segmentation_id, network_type, **kwargs):
        LOG.debug("Deploy_link on %s" % interface.get('name'))
        network_id = kwargs.get('vnetwork')

        if network_id not in self.local_vlan_map:
            self.provision_local_vlan(network_id, 'local', None, None)

        lvid = self.local_vlan_map.get(network_id).vlan

        if network_type == const.VLAN:
            if not self.enable_tunneling:
                self._local_vlan_for_vlan(lvid, const.VLAN, segmentation_id)
            else:
                return "ERROR - Tunneling enabled."

        elif network_type == const.GRE:
            remote_ip = kwargs.get('remote_ip')
            td = network_type + network_id[:4]
            port_name = self.get_tunnel_name(
                td, self.local_ip, remote_ip)
            self.int_br.add_external_tunnel_port(port_name,
                                                 remote_ip,
                                                 self.local_ip,
                                                 lvid=lvid,
                                                 tid=segmentation_id)
        return const.OK

    def undeploy_link(self, ctxt, interface, node, network_type, segmentation_id, **kwargs):

        LOG.debug("Undeploy_link on %s" % interface.get('name'))
        network_id = kwargs.get('vnetwork')

        lvid = self.local_vlan_map.get(network_id).vlan

        if network_type == const.VLAN:
            self.reclaim_local_vlan(network_id)

        elif network_type == const.GRE:
            remote_ip = kwargs.get('remote_ip')
            td = network_type + network_id[:4]
            port_name = self.get_tunnel_name(
                td, self.local_ip, remote_ip)
            self.int_br.delete_external_tunnel_port(port_name,
                                                    lvid=lvid)
        return const.OK
