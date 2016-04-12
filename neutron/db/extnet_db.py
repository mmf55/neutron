import sqlalchemy as sa
from neutron.db import model_base
from neutron.db import models_v2
from sqlalchemy import orm


class ExtInterface(model_base.BASEV2, models_v2.HasId, models_v2.HasTenant):
    __tablename__ = "extinterface"

    # The type here can be e.g. SSID, port.
    type = sa.column(sa.String(36))
    network_id = sa.Column(sa.String(36),
                           sa.ForeignKey('networks.id', ondelete='CASCADE'))
    extnode = sa.Column(sa.String(36), sa.ForeignKey("extnode.id",
                                                     ondelete="CASCADE"))


class ExtNode(model_base.BASEV2, models_v2.HasId):
    __tablename__ = "extnode"

    # type here can be e.g. router, switch, virtual switch.
    name = sa.Column(sa.String(36))
    type = sa.column(sa.String(36))


class ExtNodeInt(model_base.BASEV2, models_v2.HasId):
    __tablename__ = "extnodeint"

    name = sa.Column(sa.String(36))
    type = sa.Column(sa.String(36))
    extnode = sa.Column(sa.String(36), sa.ForeignKey("extnode.id",
                                                     ondelete="CASCADE"))
    extsegment = sa.Column(sa.String(36), sa.ForeignKey("extsegment.id",
                                                        ondelete="CASCADE"))


class ExtSegment(model_base.BASEV2, models_v2.HasId):
    __tablename__ = "extsegment"

    name = sa.column(sa.String(36))

    # Types supported can be e.g. VLAN, GRE, VXLAN.
    types_supported = sa.Column(sa.String(36))
    ids_pool = sa.Column(sa.String(36))


class ExtLink(model_base.BASEV2, models_v2.HasId):
    __tablename__ = "extlink"

    # Tells the type of the links created e.g. VLAN, GRE, VXLAN
    type = sa.column(sa.String(36))
    network_id = sa.Column(sa.String(36),
                           sa.ForeignKey('networks.id', ondelete='CASCADE'))
    overlay_id = sa.Column(sa.String(36))
    extsegment = sa.Column(sa.String(36), sa.ForeignKey("extsegment.id",
                                                        ondelete="CASCADE"))


class ExtConnection(model_base.BASEV2, models_v2.HasId):
    __tablename__ = "extconnection"

    extnodeint1 = sa.Column(sa.String(36), sa.ForeignKey("extnodeint.id",
                                                      ondelete="CASCADE"))
    extnodeint2 = sa.Column(sa.String(36), sa.ForeignKey("extnodeint.id",
                                                      ondelete="CASCADE"))
    extlink = sa.Column(sa.String(36), sa.ForeignKey("extlink.id",
                                                     ondelete="CASCADE"))
