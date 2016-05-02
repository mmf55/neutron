
from neutron_lib import exceptions


class ExtNodeIntNotFound(exceptions.NotFound):
    message = _("External node interface %(id)s could not be found.")


class ExtNodeIntHasConnectionsInUse(exceptions.InUse):
    message = _("External node %(id)s has connections in use.")


class ExtConnectionNotFound(exceptions.NotFound):
    message = _("External segment %(id)s could not be found.")


class ExtConnectionHasLinksInUse(exceptions.InUse):
    message = _("External segment %(id)s has links in use.")


class ExtLinkNotFound(exceptions.NotFound):
    message = _("External link %(id)s could not be found.")


class ExtPortNotFound(exceptions.NotFound):
    message = _("External port %(id)s could not be found.")


class ExtConnectionsExists(exceptions.NotFound):
    message = _("External connection %(id)s already exists.")
