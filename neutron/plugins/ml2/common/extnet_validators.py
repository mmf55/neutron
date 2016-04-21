import re

from neutron.plugins.common import extnet_constants

from neutron._i18n import _


def validate_types_supported(data, valid_values=None):
    if data != extnet_constants.TYPE_SUPPORTED_SEG_GRE and \
                    data != extnet_constants.TYPE_SUPPORTED_SEG_VLAN and \
                    data != extnet_constants.TYPE_SUPPORTED_SEG_VXLAN:
        return _("Invalid external network type. Valid type are: vlan, vxlan and gre.")
    return


def validate_ids_pool(data, valid_values=None):
    r1 = re.compile('^[0-9]+:[0-9]+(,[0-9]+:[0-9]+)*$')
    if r1.match(data) is None:
        return _('The format of the pool os IDs is not correct.')
    return
