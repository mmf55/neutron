import re

from neutron.plugins.common import extnet_constants

from neutron._i18n import _


def validate_types_supported(data, valid_values=None):
    if data != extnet_constants.SEG_TYPE_VLAN and \
                    data != extnet_constants.SEG_TYPE_VXLAN and \
                    data != extnet_constants.SEG_TYPE_GRE:
        return _("Invalid external network type. Valid type are: vlan, vxlan and gre.")
    return


def validate_ids_pool(data, valid_values=None):
    if data is None:
        return
    r1 = re.compile('^[0-9]+:[0-9]+(,[0-9]+:[0-9]+)*$')
    if r1.match(data) is None:
        return _('The format of the pool IDs is not correct.')
    return
