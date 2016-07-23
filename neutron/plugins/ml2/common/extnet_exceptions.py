
from neutron_lib import exceptions
from neutron._i18n import _


class ExtNetNodeAlreadyExist(exceptions.NotFound):
    message = _("External node already exists.")


class ExtNetObjectNotFound(exceptions.NotFound):
    message = _("%(model_name) %(id)s could not be found.")


class ExtInterfaceHasLinksInUse(exceptions.InUse):
    message = _("External interface %(id)s has links in use.")


class ExtNodeHasInterfacesInUse(exceptions.InUse):
    message = _("External node %(id)s has interfaces in use.")


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
    message = _("Error applying link configurations on the devices.")


class ExtLinkSegmentationIdNotAvailable(exceptions.InvalidConfigurationOption):
    message = _("The segmentation id is not available on connection.")


class ExtInterfacesNotInSameSegment(exceptions.BadRequest):
    message = _("The interfaces are not in the same segment.")


class ExtLinkTypeNotSupportedOnSegment(exceptions.InvalidInput):
    message = _("The link type requested is not supported on this segment.")


class ExtLinkTypeNotSupportedByInterfaces(exceptions.BadRequest):
    message = _("The link type requested is not supported by one or both the interfaces.")


class ExtPortErrorApplyingConfigs(exceptions.BadRequest):
    message = _("Error applying port configurations on the devices.")


class ExtInterfaceHasPortsInUse(exceptions.NotFound):
    message = _("External interface has ports in use.")


class ExtLinkErrorInSetSegID(exceptions.NotFound):
    message = _("Error returning the segmentation ID to the available pool.")


class ExtSegmentHasNoLinks(exceptions.NotFound):
    message = _("Segment has no links deployed.")


class ExtNodeErrorOnTopologyDiscover(exceptions.NotAuthorized):
    message = _("Error when discovering the network topology.")


class ExtLinkErrorObtainingSegmentationID(exceptions.NetworkNotFound):
    message = _("Error when getting the segmentation ID.")