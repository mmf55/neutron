import sqlalchemy as sa
from neutron.db import model_base
from neutron.db import models_v2
from sqlalchemy import orm


class ExtPort(model_base.BASEV2):
    __tablename__ = "extports"

    id = sa.Column(sa.String(36),
                   sa.ForeignKey("ports.id",
                                 ondelete="CASCADE"),
                   primary_key=True)
    segmentation_id = sa.Column(sa.String(36))
    extinterface_id = sa.Column(sa.String(36), sa.ForeignKey("extinterfaces.id",
                                                             ondelete="CASCADE"))
    extinterface = orm.relationship("ExtInterface",
                                    back_populates='extports')
    port = orm.relationship(models_v2.Port)


class ExtInterface(model_base.BASEV2, models_v2.HasId):
    __tablename__ = "extinterfaces"

    name = sa.Column(sa.String(36))
    # l2, l3
    type = sa.Column(sa.String(36))
    ip_address = sa.Column(sa.String(36))
    node_name = sa.Column(sa.String(36))
    node_driver = sa.Column(sa.String(36))

    extsegment_id = sa.Column(sa.String(36),
                              sa.ForeignKey('extsegments.id', ondelete="CASCADE"))

    extsegment = orm.relationship("ExtSegment",
                                  back_populates='extinterfaces',
                                  cascade='all,delete')

    extports = orm.relationship("ExtPort",
                                back_populates='extinterface')


class ExtSegment(model_base.BASEV2, models_v2.HasId):
    __tablename__ = "extsegments"

    name = sa.Column(sa.String(36))
    types_supported = sa.Column(sa.String(36))
    vlan_ids_available = sa.Column(sa.String(36))
    tun_ids_available = sa.Column(sa.String(36))

    extinterfaces = orm.relationship("ExtInterface",
                                     back_populates='extsegment')


class ExtLink(model_base.BASEV2, models_v2.HasId):
    __tablename__ = "extlinks"

    name = sa.Column(sa.String(36))
    # Tells the type of the links created e.g. VLAN, GRE, VXLAN
    type = sa.Column(sa.String(36))
    segmentation_id = sa.Column(sa.String(36))

    extinterface1_id = sa.Column(sa.String(36), sa.ForeignKey("extinterfaces.id",
                                                              ondelete="CASCADE"))
    extinterface2_id = sa.Column(sa.String(36), sa.ForeignKey("extinterfaces.id",
                                                              ondelete="CASCADE"))

    network_id = sa.Column(sa.String(36), sa.ForeignKey("networks.id"),
                           nullable=False)
