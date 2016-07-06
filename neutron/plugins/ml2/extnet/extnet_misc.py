import itertools
import oslo_messaging
from oslo_log import log as logging

from neutron.callbacks import registry, resources, events
from neutron.common import topics
from neutron.common import rpc as n_rpc
from neutron.plugins.ml2.common import extnet_exceptions
from neutron.plugins.ml2.extnet import config

from neutron.db import extnet_db_mixin
from neutron.db import extnet_db as models

from extnet_networkcontroller.network_controller import net_ctrl
from extnet_networkcontroller.network_controller import dev_ctrl_mgr
from extnet_networkcontroller.device_controller import dev_ctrl
from extnet_networkcontroller.common import const

from sqlalchemy import or_

LOG = logging.getLogger(__name__)


class ExtNetControllerMixin(extnet_db_mixin.ExtNetworkDBMixin,
                            net_ctrl.ExtNetController):
    def initialize_extnetcontroller(self):

        # Subscribe for the creation of new ports.
        registry.subscribe(self.create_port_callback, resources.PORT, events.AFTER_CREATE)

        device_ctrl_mgr = ExtNetDeviceCtrlManager({topics.AGENT: ['OVS'], topics.EXTNET_AGENT: ['ESW1', 'ESW2']})
        super(ExtNetControllerMixin, self).__init__(device_ctrl_mgr)

    def create_extlink(self, context, extlink):

        # Get the necessary info
        link = extlink['extlink']
        interface1 = self.get_extinterface(context, link.get('extinterface1_id'))
        interface2 = self.get_extinterface(context, link.get('extinterface2_id'))

        if interface1.get('extsegment_id') != interface2.get('extsegment_id'):
            raise extnet_exceptions.ExtInterfacesNotInSameSegment()

        segment = self.get_extsegment(context, interface1.get('extsegment_id'))

        link['segmentation_id'] = self._get_segmentation_id(context,
                                                            segment.get('id'),
                                                            link.get('type'),
                                                            link.get('network_id'))

        # Call create link to make the changes on the network.
        if self.deploy_link(link,
                            interface1,
                            interface2,
                            vnetwork=link.get('network_id'),
                            context=context) != const.OK:
            raise extnet_exceptions.ExtLinkErrorApplyingConfigs()

        # Save new link on the database
        return super(ExtNetControllerMixin, self).create_extlink(context, extlink)

    def create_port_callback(self, resource, event, trigger, **kwargs):
        context = kwargs.get('context')
        port = kwargs.get('port')
        ext_port = port.get('external_port')
        if ext_port:
            interface = self.get_extinterface(context, ext_port.get('extinterface_id'))

            self.deploy_port(interface, ext_port.get('segmentation_id'))

    # ------------------------------------ Auxiliary functions ---------------------------------------

    def _get_segmentation_id(self, context, segment_id, conn_type, network_id):
        segment = context.session.query(models.ExtSegment).filter_by(id=segment_id).first()

        if conn_type == const.VLAN:
            interfaces = context.session.query(models.ExtInterface).filter_by(extsegment_id=segment_id).all()
            for interface in interfaces:
                link = context.session.query(models.ExtLink) \
                    .filter_by(or_(models.ExtLink.extinterface1_id == interface.id,
                                   models.ExtLink.extinterface2_id == interface.id)) \
                    .filter_by(models.ExtLink.type == const.VLAN) \
                    .filter_by(models.ExtLink.network_id == network_id) \
                    .first()
                if link:
                    return link.segmentation_id
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


class ExtNetDeviceCtrlManager(dev_ctrl_mgr.ExtNetDeviceControllerManager):
    def __init__(self, config):
        super(ExtNetDeviceCtrlManager, self).__init__(config)

    def deploy_link_on_node(self, interface, network_type, segmentation_id, **kwargs):
        context = kwargs.get('context')
        node = interface['node_name']
        topic = self.get_device_controller(node)
        topic_create_extlink = topics.get_topic_name(topic,
                                                     topics.EXTNET_LINK,
                                                     topics.CREATE)
        target = oslo_messaging.Target(topic=topic, version='1.0')
        client = n_rpc.get_client(target)
        cctxt = client.prepare(topic=topic_create_extlink,
                               fanout=False,
                               timeout=5)
        return cctxt.call(context,
                          'deploy_link',
                          network_type=network_type,
                          segmentation_id=segmentation_id,
                          interface=interface,
                          vnetwork=kwargs.get('vnetwork'))

    def deploy_port_on_node(self, interface, segmentation_id, **kwargs):
        context = kwargs.get('context')
        node = interface['node_name']
        topic = self.get_device_controller(node)
        topic_create_extport = topics.get_topic_name(topic,
                                                     topics.EXTNET_PORT,
                                                     topics.CREATE)
        target = oslo_messaging.Target(topic=topic, version='1.0')
        client = n_rpc.get_client(target)
        cctxt = client.prepare(topic=topic_create_extport,
                               fanout=False,
                               timeout=5)

        return cctxt.call(context,
                          'deploy_port',
                          segmentation_id=segmentation_id,
                          interface=interface,
                          vnetwork=kwargs.get('vnetwork'))


class ExtNetOVSAgentMixin(dev_ctrl.ExtNetDeviceController):
    def deploy_link(self, ctxt, interface, network_type, segmentation_id, **kwargs):
        LOG.debug("Deploy_link called!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        return
        network_id = kwargs.get('vnetwork')

        if network_id not in self.local_vlan_map:
            self.provision_local_vlan(network_id, 'local', None, None)

        lvid = self.local_vlan_map.get(network_id).vlan

        if network_type == const.VLAN:
            if not self.enable_tunneling:
                self._local_vlan_for_vlan(lvid, const.VLAN, segmentation_id)
            else:
                return "ERROR - Tunneling not enabled."

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
