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
    extinterface_id = sa.Column(sa.String(36), sa.ForeignKey("extinterfaces.id"))
    extinterface = orm.relationship("ExtInterface",
                                    back_populates='extports')
    # port = orm.relationship(models_v2.Port)

    port = orm.relationship(
        models_v2.Port,
        backref=orm.backref("extport", uselist=False,
                            cascade='delete', lazy='joined'))


class ExtNode(model_base.BASEV2, models_v2.HasId):
    __tablename__ = "extnodes"

    name = sa.Column(sa.String(36))
    ip_address = sa.Column(sa.String(36))

    extinterfaces = orm.relationship("ExtInterface",
                                     back_populates='extnode')


class ExtInterface(model_base.BASEV2, models_v2.HasId):
    __tablename__ = "extinterfaces"

    name = sa.Column(sa.String(36))
    # l2, l3
    type = sa.Column(sa.String(36))
    ip_address = sa.Column(sa.String(36))
    # node_name = sa.Column(sa.String(36))
    # node_driver = sa.Column(sa.String(36))
    extnode_id = sa.Column(sa.String(36),
                           sa.ForeignKey('extnodes.id'))

    extsegment_id = sa.Column(sa.String(36),
                              sa.ForeignKey('extsegments.id'))

    extnode = orm.relationship("ExtNode",
                               back_populates='extinterfaces')

    extsegment = orm.relationship("ExtSegment",
                                  back_populates='extinterfaces')

    extports = orm.relationship("ExtPort",
                                back_populates='extinterface')


class ExtSegment(model_base.BASEV2, models_v2.HasId):
    __tablename__ = "extsegments"

    name = sa.Column(sa.String(36))
    type_supported = sa.Column(sa.String(36))
    ids_available = sa.Column(sa.String(36))

    extinterfaces = orm.relationship("ExtInterface",
                                     back_populates='extsegment')


class ExtLink(model_base.BASEV2, models_v2.HasId):
    __tablename__ = "extlinks"

    name = sa.Column(sa.String(36))
    segmentation_id = sa.Column(sa.String(36))

    extinterface1_id = sa.Column(sa.String(36), sa.ForeignKey("extinterfaces.id"))
    extinterface2_id = sa.Column(sa.String(36), sa.ForeignKey("extinterfaces.id"))

    network_id = sa.Column(sa.String(36), sa.ForeignKey("networks.id"),
                           nullable=False)
