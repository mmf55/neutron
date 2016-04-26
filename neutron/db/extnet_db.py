import sqlalchemy as sa
from neutron.db import model_base
from neutron.db import models_v2
from sqlalchemy import orm


class ExtInterface(model_base.BASEV2, models_v2.HasId, models_v2.HasTenant):
    __tablename__ = "extinterfaces"

    name = sa.Column(sa.String(36))
    # The type here can be e.g. SSID, VLAN, physical port.
    type = sa.Column(sa.String(36))
    # The access ID can be e.g. VNID, SSID.
    access_id = sa.Column(sa.String(36))
    network_id = sa.Column(sa.String(36),
                           sa.ForeignKey('networks.id', ondelete='CASCADE'))
    extnode_id = sa.Column(sa.String(36), sa.ForeignKey("extnodes.id",
                                                        ondelete="CASCADE"))


class ExtNode(model_base.BASEV2, models_v2.HasId):
    __tablename__ = "extnodes"

    name = sa.Column(sa.String(36))
    # type here can be e.g. router, switch, virtual switch.
    type = sa.Column(sa.String(36))
    extnodeints = orm.relationship(ExtNodeInt,
                                   backref='extnodeints',
                                   cascade='all,delete')


class ExtNodeInt(model_base.BASEV2, models_v2.HasId):
    __tablename__ = "extnodeints"

    name = sa.Column(sa.String(36))
    extnode_id = sa.Column(sa.String(36), sa.ForeignKey("extnodes.id",
                                                        ondelete="CASCADE"))
    extsegment_id = sa.Column(sa.String(36), sa.ForeignKey("extsegments.id",
                                                           ondelete="CASCADE"))


class ExtSegment(model_base.BASEV2, models_v2.HasId):
    __tablename__ = "extsegments"

    name = sa.Column(sa.String(36))
    # Types supported can be e.g. VLAN, GRE, VXLAN.
    types_supported = sa.Column(sa.String(36))
    ids_pool = sa.Column(sa.String(36))


class ExtLink(model_base.BASEV2, models_v2.HasId):
    __tablename__ = "extlinks"

    # Tells the type of the links created e.g. VLAN, GRE, VXLAN
    type = sa.Column(sa.String(36))
    network_id = sa.Column(sa.String(36),
                           sa.ForeignKey('networks.id', ondelete='CASCADE'))
    overlay_id = sa.Column(sa.String(36))
    extsegment_id = sa.Column(sa.String(36), sa.ForeignKey("extsegments.id",
                                                           ondelete="CASCADE"))


class ExtConnection(model_base.BASEV2, models_v2.HasId):
    __tablename__ = "extconnections"

    # Connection types can be e.g. normal or trunk.
    type = sa.Column(sa.String(36))

    extnodeint1_id = sa.Column(sa.String(36), sa.ForeignKey("extnodeints.id",
                                                            ondelete="CASCADE"))
    extnodeint2_id = sa.Column(sa.String(36), sa.ForeignKey("extnodeints.id",
                                                            ondelete="CASCADE"))
    extlink_id = sa.Column(sa.String(36), sa.ForeignKey("extlinks.id",
                                                        ondelete="CASCADE"))
