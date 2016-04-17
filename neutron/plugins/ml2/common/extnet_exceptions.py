
from neutron_lib import exceptions


class ExtNodeNotFound(exceptions.NotFound):
    message = _("External node %(id)s could not be found.")


class ExtNodeHasConnectionsInUse(exceptions.InUse):
    message = _("External node %(id)s has connections in use.")


class ExtSegmentNotFound(exceptions.NotFound):
    message = _("External segment %(id)s could not be found.")


class ExtSegmentHasLinksInUse(exceptions.InUse):
    message = _("External segment %(id)s has links in use.")


class ExtLinkNotFound(exceptions.NotFound):
    message = _("External link %(id)s could not be found.")


class ExtInterfaceNotFound(exceptions.NotFound):
    message = _("External interface %(id)s could not be found.")
