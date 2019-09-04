# Django
from django.db.models import Q, F
from django.db.models import Avg, Count, Max, Min, StdDev, Sum, Variance

# Rest framework
from rest_framework import permissions, views
from rest_framework.response import Response

# Project
from .clickhouse import ClickHouse
from .models import Frame, Metadata


class QueryPostgreSQL(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        params = self.request.query_params

        # Metadatas
        # TODO Optimize using data__contains when key does not end by __gte/__lte
        # because __contains will trigger usage of the GIN index.
        kw = {}
        exclude = {
            'format',                   # From Django Rest framework
            'fields', 'tags',           # Columns
            'limit',
            'time__gte', 'time__lte',   # Time range
            'interval', 'interval_agg', # Aggregated results
        }
        for key, value in params.items():
            if key not in exclude:
                if key.endswith(':int'):
                    key = key[:-4]
                    value = int(value)

                kw[key] = value

        metadatas = Metadata.filter(**kw)
        metadatas = list(metadatas.values_list('id', flat=True))

        args, kw = [], {}

        # Frames
        queryset = Frame.objects.filter(metadata__in=metadatas)
        for key in 'time__gte', 'time__lte':
            value = params.get(key)
            if value is not None:
                kw[key] = int(float(value))

        # Fields
        fields = params.getlist('fields')
        if fields:
            if len(fields) == 1:
                q = Q(data__has_key=fields[0])
            else:
                q = Q(data__has_any_keys=fields)

            # Fields defined in the schema
            for field in set(fields) & set(Frame.get_data_fields()):
                q |= Q(**{'%s__isnull' % field: False})

            args.append(q)

        queryset = queryset.filter(*args, **kw)
        queryset = queryset.order_by('time')

        # Interval
        interval = params.get('interval')
        if interval:
            # XXX Interval and tags don't work together (TEST)
            # XXX Interval requires fields (TEST)
            interval = int(interval)
            interval_agg = params.get('interval_agg', 'avg')
            agg = {
                'avg': Avg,
                'count': Count,
                'max': Max,
                'min': Min,
                'stddev': StdDev,
                'sum': Sum,
                'variance': Variance,
            }[interval_agg]
            annotations = {x: agg(x) for x in fields}
            queryset = queryset\
                .annotate(key=(F('time') / interval) * interval)\
                .values('key')\
                .annotate(time=F('key'), **annotations)

        tags = params.getlist('tags')
        return queryset.select_related('metadata') if tags else queryset

    def get(self, request, format=None):
        params = self.request.query_params
        queryset = self.get_queryset()

        # Limit
        limit = params.get('limit')
        if limit:
            limit = int(limit)
            queryset = queryset[:limit]

        fields = params.getlist('fields')
        tags = params.getlist('tags')

        if fields:
            columns = ['time'] + fields
            rows = []
            for obj in queryset:
                if type(obj) is dict:
                    row = [obj[x] for x in columns]
                else:
                    row = [obj.get_value(x) for x in columns]

                if tags:
                    metadata = obj.metadata
                    for tag in tags:
                        value = metadata.tags.get(tag)
                        row.append(value)

                rows.append(row)

            return Response({'columns': columns + tags, 'rows': rows, 'format': 'compact'})

        # If fields are not specified we'll use the sparse format
        data_fields = Frame.get_data_fields()
        rows = []
        for obj in queryset:
            if type(obj) is dict:
                row = obj
            else:
                row = {}
                for name in data_fields:
                    value = obj.get_value(name)
                    if value is not None:
                        row[name] = value
                if obj.data:
                    row.update(obj.data)

            if tags:
                metadata = obj.metadata
                for tag in tags:
                    value = metadata.get_value(tag)
                    row[tag] = value

            rows.append(row)

        return Response({'rows': rows, 'format': 'sparse'})


class QueryClickHouse(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, format=None):
        params = self.request.query_params
        table = params['table']

        limit = params.get('limit')
        columns = params.getlist('fields')
        interval = params.get('interval')
        interval_agg = params.get('interval_agg', 'avg')

        time__gte = params.get('time__gte')
        time__lte = params.get('time__lte')
        if time__lte and time__gte:
            assert time__gte < time__lte

        # Time range
        where = []
        if time__gte:
            where.append(f'TIMESTAMP >= {time__gte}')
        if time__lte:
            where.append(f'TIMESTAMP <= {time__lte}')
        where = ' AND '.join(where)

        with ClickHouse() as clickhouse:
            # No columns, all columns (useful to check available columns)
            if not columns:
                columns = clickhouse.select(
                    'system.columns', columns=['name'],
                    where=f"database = 'wsn' AND table = '{table}'",
                    order_by='name',
                )
                columns = [name for name, in columns]

            # Average over interval
            if interval:
                time_column = f'intDiv(TIMESTAMP, {interval}) * {interval} AS time'
                columns = [f'{interval_agg}({x}) AS {x}' for x in columns]
                group_by = 'time'
            else:
                time_column = 'TIMESTAMP AS time'
                group_by = None

            # Get data
            columns = [time_column] + columns
            rows, columns = clickhouse.select(
                table, columns=columns, where=where,
                group_by=group_by, order_by='time', limit=limit,
                with_column_types=True,
            )
            columns = [name for name, typ in columns]

        return Response({'columns': columns, 'rows': rows, 'format': 'compact'})
