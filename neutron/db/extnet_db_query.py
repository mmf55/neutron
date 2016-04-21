from neutron.db import models_v2
from neutron.plugins.ml2 import driver_api as api

from neutron_lib import exceptions
import sqlalchemy as sa
from sqlalchemy.orm import exc


class ExtNetworkCommonDbMixin(object):

    def _apply_filters_to_query(self, query, model, filters):
        """Apply filters to query for the models."""
        if filters:
            for key, value in filters.iteritems():
                column = getattr(model, key, None)
                if column:
                    query = query.filter(column.in_(value))
        return query

    def _model_query(self, context, model):
        """Query model based on filter."""
        query = context.session.query(model)
        query_filter = None
        if not context.is_admin and hasattr(model, 'tenant_id'):
            if hasattr(model, 'shared'):
                query_filter = ((model.tenant_id == context.tenant_id) |
                                (model.shared == sa.true()))
            else:
                query_filter = (model.tenant_id == context.tenant_id)
        if query_filter is not None:
            query = query.filter(query_filter)
        return query

    def _get_collection_query(self, context, model, filters=None,
                              sorts=None, limit=None, marker_obj=None,
                              page_reverse=False):
        """Get collection query for the models."""
        collection = self._model_query(context, model)
        collection = self._apply_filters_to_query(collection, model, filters)
        return collection

    def _get_collection(self, context, model, dict_func, filters=None,
                        fields=None, sorts=None, limit=None, marker_obj=None,
                        page_reverse=False):
        """Get collection object based on query for resources."""
        query = self._get_collection_query(context, model, filters=filters,
                                           sorts=sorts,
                                           limit=limit,
                                           marker_obj=marker_obj,
                                           page_reverse=page_reverse)
        items = [dict_func(c, fields) for c in query]
        if limit and page_reverse:
            items.reverse()
        return items
