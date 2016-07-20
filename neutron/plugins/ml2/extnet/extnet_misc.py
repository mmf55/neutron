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
from neutron.plugins.ml2.extnet.topology_discovery import topo_discovery

from neutron.db import extnet_db_mixin
from neutron.db import extnet_db as models

from extnet_networkcontroller.network_controller import net_ctrl
from extnet_networkcontroller.network_controller import dev_ctrl_mgr
from extnet_networkcontroller.device_controller import dev_ctrl
from extnet_networkcontroller.common import const

from sqlalchemy import or_

LOG = logging.getLogger(__name__)


# This class holds the main logic for extending the virtual networks to the campus network.
class ExtNetControllerMixin(extnet_db_mixin.ExtNetworkDBMixin,
                            net_ctrl.ExtNetController):
    def initialize_extnetcontroller(self):

        config_dict = {device_ctrl: dev_name_list.split(';')
                       for device_ctrl, dev_name_list in cfg.CONF.EXTNET_CONTROLLER.device_controllers.items()}

        device_ctrl_mgr = ExtNetDeviceCtrlManager(config_dict)

        registry.subscribe(self.delete_extport, resources.PORT, events.BEFORE_DELETE)

        super(ExtNetControllerMixin, self).__init__(device_ctrl_mgr)

    def create_extnode(self, context, extnode):
        node = extnode['extnode']

        if node.get('topology_discover'):
            td = topo_discovery.TopologyDiscovery()
            topo_dict = td.get_devices_info(node.get('ip_address'))
            nodes_created = []
            for node, node_info_dict in topo_dict.items():
                if self.get_extnode_by_name(context, node):
                    continue
                node_dict = dict(name=node,
                                 ip_address=node_info_dict.get('ip_address'))
                node_dict = {'extnode': node_dict}
                node_created = super(ExtNetControllerMixin, self).create_extnode(context, node_dict)
                nodes_created.append(node_created)

                for interface in node_info_dict.get('interfaces'):
                    p = re.compile("^FastEthernet")
                    if p.match(interface.get('name')):
                        if interface.get('ip_address') is not None:
                            net_type = 'l3'
                        else:
                            net_type = 'l2'
                        interface_dict = dict(name=interface.get('name'),
                                              ip_address=interface.get('ip_address'),
                                              type=net_type,
                                              extnode_id=node_created.get('id')
                                              )
                        interface_dict = {'extinterface': interface_dict}
                        super(ExtNetControllerMixin, self).create_extinterface(context, interface_dict)
            if nodes_created:
                return nodes_created[-1]
            else:
                raise extnet_exceptions.ExtNetNodeAlreadyExist()
        else:
            return super(ExtNetControllerMixin, self).create_extnode(context, extnode)

    def create_extlink(self, context, extlink):

        # Get the necessary info
        link = extlink['extlink']
        interface1 = self.get_extinterface(context, link.get('extinterface1_id'))
        interface2 = self.get_extinterface(context, link.get('extinterface2_id'))

        node1 = self.get_extnode(context, interface1.get('extnode_id'))
        node2 = self.get_extnode(context, interface2.get('extnode_id'))

        if self._extinterface_has_extports(context, interface1.get('id')) \
                or self._extinterface_has_extports(context, interface2.get('id')):
            raise extnet_exceptions.ExtInterfaceHasPortsInUse()

        if interface1.get('extsegment_id') != interface2.get('extsegment_id'):
            raise extnet_exceptions.ExtInterfacesNotInSameSegment()

        segment = self.get_extsegment(context, interface1.get('extsegment_id'))

        if link.get('type') not in segment.get('types_supported').split(','):
            raise extnet_exceptions.ExtLinkTypeNotSupportedOnSegment()

        if (link.get('type') == const.GRE and not (interface1.get('type') == 'l3' and
                                                           interface2.get('type') == 'l3')) or \
                (link.get('type') == const.VLAN and not (interface1.get('type') == 'l2' and
                                                                 interface2.get('type') == 'l2')):
            raise extnet_exceptions.ExtLinkTypeNotSupportedByInterfaces()

        link['segmentation_id'] = self._get_segmentation_id(context,
                                                            segment.get('id'),
                                                            link.get('type'),
                                                            link.get('network_id'))

        # Call create link to make the changes on the network.
        # if self.deploy_link(link,
        #                     interface1,
        #                     interface2,
        #                     node1,
        #                     node2,
        #                     vnetwork=link.get('network_id'),
        #                     context=context) != const.OK:
        #     raise extnet_exceptions.ExtLinkErrorApplyingConfigs()

        # Save new link on the database
        return super(ExtNetControllerMixin, self).create_extlink(context, extlink)

    def delete_extlink(self, context, id):
        link = self.get_extlink(context, id)

        interface1 = self.get_extinterface(context, link.get('extinterface1_id'))
        interface2 = self.get_extinterface(context, link.get('extinterface2_id'))

        node1 = self.get_extnode(context, interface1.get('extnode_id'))
        node2 = self.get_extnode(context, interface2.get('extnode_id'))

        segment = self.get_extsegment(context, interface1.get('extsegment_id'))

        # if self.undeploy_link(link,
        #                       interface1,
        #                       interface2,
        #                       node1,
        #                       node2,
        #                       vnetwork=link.get('network_id'),
        #                       context=context) != const.OK:
        #     raise extnet_exceptions.ExtLinkErrorApplyingConfigs()

        if self._set_segmentation_id(context,
                                     link.get('segmentation_id'),
                                     segment.get('id'),
                                     link.get('type'),
                                     link.get('network_id')) != const.OK:
            raise extnet_exceptions.ExtLinkErrorInSetSegID()

        return super(ExtNetControllerMixin, self).delete_extlink(context, id)

    def create_extport(self, context, port):
        port = port.get('port')
        ext_port = port.get('external_port')[0]
        interface = self.get_extinterface(context, ext_port.get('extinterface_id'))

        if self._extinterface_has_extlinks(context, interface.get('id')):
            raise extnet_exceptions.ExtPortErrorApplyingConfigs()

        interface_extports = self._extinterface_has_extports(context, interface.get('id'))
        if interface_extports:
            if next((x for x in interface_extports if x.port.network_id != port.get('network_id'))):
                raise extnet_exceptions.ExtPortErrorApplyingConfigs()

        if interface.get('type') == 'l2':
            links = self._get_all_links_on_extsegment_by_type(context,
                                                              interface.get('extsegment_id'),
                                                              const.VLAN,
                                                              port.get('network_id'))
            if links:
                ext_port['segmentation_id'] = links[0].segmentation_id
            else:
                raise extnet_exceptions.ExtLinkSegmentationIdNotAvailable()

        elif interface.get('type') == 'l3':
            ext_port['segmentation_id'] = None

        if not interface_extports:
            if self.deploy_port(interface,
                                ext_port.get('segmentation_id'),
                                context=context) != const.OK:
                raise extnet_exceptions.ExtPortErrorApplyingConfigs()

    def delete_extport(self, context, port):
        port = self.get_extport(context, port.get('port_id'))
        if port:
            interface = self.get_extinterface(context, port.get('extinterface_id'))
            if self.undeploy_port(interface,
                                  port.get('segmentation_id'),
                                  context=context) != const.OK:
                raise extnet_exceptions.ExtPortErrorApplyingConfigs()

    # ------------------------------------ Auxiliary functions ---------------------------------------

    def _extinterface_has_extports(self, context, interface_id):
        interface = context.session.query(models.ExtInterface).filter_by(id=interface_id).first()
        return interface.extports

    def _extinterface_has_extlinks(self, context, interface_id):
        links = context.session.query(models.ExtLink) \
            .filter(or_(models.ExtLink.extinterface1_id == interface_id,
                        models.ExtLink.extinterface2_id == interface_id)) \
            .all()
        return links

    def _get_all_links_on_extsegment_by_type(self, context, segment_id, conn_type, network_id):
        interfaces = context.session.query(models.ExtInterface).filter_by(extsegment_id=segment_id).all()
        links = []
        for interface in interfaces:
            links += context.session.query(models.ExtLink) \
                .filter(or_(models.ExtLink.extinterface1_id == interface.id,
                            models.ExtLink.extinterface2_id == interface.id)) \
                .filter(models.ExtLink.type == conn_type) \
                .filter(models.ExtLink.network_id == network_id) \
                .all()
            links = list(set(links))
        return links

    def _get_segmentation_id(self, context, segment_id, conn_type, network_id):
        segment = context.session.query(models.ExtSegment).filter_by(id=segment_id).first()

        if conn_type == const.VLAN:
            links = self._get_all_links_on_extsegment_by_type(context, segment_id, const.VLAN, network_id)
            if links:
                return links[0].segmentation_id

            ids_avail = segment.vlan_ids_available
        else:
            ids_avail = segment.tun_ids_available

        # [(123, 130), (1000, 2000)]
        l = [[int(ids.split(':')[0]), int(ids.split(':')[1])]
             if len(ids.split(':')) > 1 else [int(ids)] for ids in ids_avail.split(',')]

        num_list = list()
        for item in l:
            if len(item) > 1:
                num_list += range(item[0], item[1] + 1)
            else:
                num_list += item

        num_list.sort()

        seg_id = num_list.pop(0)

        l2 = [':'.join([str(t[0][1]), str(t[-1][1])]) if t[0][1] - t[-1][1] != 0 else str(t[0][1]) for t in
              (tuple(g[1]) for g in itertools.groupby(enumerate(num_list), lambda (i, x): i - x))]

        if conn_type == const.VLAN:
            segment.vlan_ids_available = ','.join(l2)
        else:
            segment.tun_ids_available = ','.join(l2)

        return seg_id

    def _set_segmentation_id(self, context, id_to_set, segment_id, conn_type, network_id):

        segment = context.session.query(models.ExtSegment).filter_by(id=segment_id).first()

        if conn_type == const.VLAN:
            links = self._get_all_links_on_extsegment_by_type(context, segment_id, const.VLAN, network_id)
            links = {x for x in links if x['segmentation_id'] != id_to_set}
            if links:
                return const.OK
            ids_avail = segment.vlan_ids_available
        else:
            ids_avail = segment.tun_ids_available

        # [(123, 130), (1000, 2000)]
        l = [[int(ids.split(':')[0]), int(ids.split(':')[1])]
             if len(ids.split(':')) > 1 else [int(ids)] for ids in ids_avail.split(',')]

        num_list = list()
        for item in l:
            if len(item) > 1:
                num_list += range(item[0], item[1] + 1)
            else:
                num_list += item

        num_list.append(int(id_to_set))
        num_list.sort()

        l2 = [':'.join([str(t[0][1]), str(t[-1][1])]) if t[0][1] - t[-1][1] != 0 else str(t[0][1]) for t in
              (tuple(g[1]) for g in itertools.groupby(enumerate(num_list), lambda (i, x): i - x))]

        if conn_type == const.VLAN:
            segment.vlan_ids_available = ','.join(l2)
        else:
            segment.tun_ids_available = ','.join(l2)

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
            port_name = self.get_tunnel_name(
                network_type, self.local_ip, remote_ip)
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
            port_name = self.get_tunnel_name(
                network_type, self.local_ip, remote_ip)
            self.int_br.delete_external_tunnel_port(port_name,
                                                    lvid=lvid)
        return const.OK
