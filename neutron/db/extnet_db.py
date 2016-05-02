import sqlalchemy as sa
from neutron.db import model_base
from neutron.db import models_v2
from sqlalchemy import orm


class ExtPort(model_base.BASEV2):
    __tablename__ = "extports"

    port_id = sa.Column(sa.String(36),
                        sa.ForeignKey('ports.id', ondelete="CASCADE"),
                        primary_key=True)
    # The access ID can be e.g. VNID, SSID.
    access_id = sa.Column(sa.String(36))
    extnodeint_id = sa.Column(sa.String(36), sa.ForeignKey("extnodeints.id",
                                                           ondelete="CASCADE"))
    extnodeint = orm.relationship(
        "ExtNodeInt",
        backref=orm.backref('extport', uselist=False))
    port = orm.relationship(
        models_v2.Port,
        backref=orm.backref("extport", uselist=False,
                            cascade='delete', lazy='joined'))


class ExtNodeInt(model_base.BASEV2, models_v2.HasId):
    __tablename__ = "extnodeints"

    name = sa.Column(sa.String(36))
    type = sa.Column(sa.String(36))
    extnodename = sa.Column(sa.String(36))


class ExtConnection(model_base.BASEV2, models_v2.HasId):
    __tablename__ = "extconnections"

    types_supported = sa.Column(sa.String(36))
    ids_pool = sa.Column(sa.String(36))
    extnodeint1_id = sa.Column(sa.String(36), sa.ForeignKey("extnodeints.id",
                                                            ondelete="CASCADE"))
    extnodeint2_id = sa.Column(sa.String(36), sa.ForeignKey("extnodeints.id",
                                                            ondelete="CASCADE"))


class ExtLink(model_base.BASEV2, models_v2.HasId):
    __tablename__ = "extlinks"

    # Tells the type of the links created e.g. VLAN, GRE, VXLAN
    type = sa.Column(sa.String(36))
    overlay_id = sa.Column(sa.String(36))
    extport_id = sa.Column(sa.String(36),
                           sa.ForeignKey('extports.port_id', ondelete="CASCADE"))
    extconnection_id = sa.Column(sa.String(36),
                                 sa.ForeignKey('extconnections.id', ondelete="CASCADE"))
    extport = orm.relationship("ExtPort",
                               backref='extlinks',
                               cascade='all,delete')
    extconnection = orm.relationship("ExtConnection",
                                     backref='extlinks',
                                     cascade='all,delete')
