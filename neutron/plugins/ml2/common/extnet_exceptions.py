
from neutron_lib import exceptions
from neutron._i18n import _


class ExtNetObjectNotFound(exceptions.NotFound):
    message = _("%(model_name) %(id)s could not be found.")


class ExtInterfaceHasLinksInUse(exceptions.InUse):
    message = _("External interface %(id)s has links in use.")


class ExtConnectionNotFound(exceptions.NotFound):
    message = _("External segment %(id)s could not be found.")


class ExtSegmentHasLinksInUse(exceptions.InUse):
    message = _("External segment %(id)s has links in use.")


class ExtLinkNotFound(exceptions.NotFound):
    message = _("External link %(id)s could not be found.")


class ExtPortNotFound(exceptions.NotFound):
    message = _("External port %(id)s could not be found.")


class ExtLinkExists(exceptions.NotFound):
    message = _("External link %(id)s already exists.")


class ExtLinkErrorApplyingConfigs(exceptions.BadRequest):
    message = _("Error applying configuration on the devices.")


class ExtLinkSegmentationIdNotAvailable(exceptions.InvalidConfigurationOption):
    message = _("The segmentation id %(segmentation_id) is not available on connection %(connection_id).")


class ExtInterfacesNotInSameSegment(exceptions.BadRequest):
    message = _("The interfaces are not in the same segment.")
