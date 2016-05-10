
from oslo_config import cfg
from oslo_log import log

from neutron.db import extnet_db
from neutron.plugins.ml2.drivers import helpers

LOG = log.getLogger(__name__)


class ExtnetTypeDriver(helpers.SegmentTypeDriver):

    def __init__(self):
        super(ExtnetTypeDriver, self).__init__(extnet_db.ExtSegment)

    def allocate_partially_specified_segment(self, session, **filters):
        return super(ExtnetTypeDriver, self).allocate_partially_specified_segment(session, **filters)

    def allocate_fully_specified_segment(self, session, **raw_segment):
        return super(ExtnetTypeDriver, self).allocate_fully_specified_segment(session, **raw_segment)
