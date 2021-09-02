# Django
from django.conf import settings
from django.contrib.postgres.fields.jsonb import KeyTextTransform
from django.db.models import FloatField
from django.db.models import Q, F
from django.db.models import Avg, Count, Max, Min, StdDev, Sum, Variance
from django.db.models.functions import Cast

# Rest framework
from rest_framework import permissions, serializers, views
from rest_framework.response import Response

# Project
from wsn.clickhouse import ClickHouse
from wsn.models import Frame, Metadata


def filter_or(queryset, *args, **kw):
    """
    Like queryset.filter(*args, **kw) but it filters using OR instead of AND.
    """
    args = list(args)
    for key, value in kw.items():
        args.append(Q(**{key: value}))

    if not args:
        return queryset

    query = args[0]
    for q in args[1:]:
        query |= q

    return queryset.filter(query)


class QueryPostgreSQL(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        params = self.request.query_params

        # Fields. Split between first class fields defined in the schema, and
        # those stored in the JSONB datatype (data->'xxx').
        fields = set(params.getlist('fields'))
        data_fields = set(Frame.get_data_fields())
        row_fields = list(fields & data_fields) # Fields defined in the schema
        json_fields = list(fields - data_fields) # Fields in the JSON datatype (data->'xxx')

        # Get list of metadatas, and filter frames by them.
        exclude = {
            'format',                           # From Django Rest framework
            'fields', 'tags',                   # Columns
            'limit',
            'time__gte', 'time__lte',           # Time range (sampled)
            'received__gte', 'received__lte',   # Time range (received, by gateway)
            'interval', 'interval_agg',         # Aggregated results
        }
        kw = {}
        for key, value in params.items():
            if key not in exclude:
                if key.endswith(':int'):
                    key = key[:-4]
                    value = int(value)

                kw[key] = value

        metadatas = Metadata.filter(**kw).values_list('id', flat=True)
        queryset = Frame.objects.filter(metadata__in=list(metadatas))

        # Filter by time range
        kw = {}
        for key in 'time__gte', 'time__lte', 'received__gte', 'received__lte':
            value = params.get(key)
            if value is not None:
                kw[key] = int(float(value))
        if kw:
            queryset = queryset.filter(**kw)

        # Filter the frames that have the fields we're looking for
        if len(json_fields) > 1:
            args = [Q(data__has_any_keys=json_fields)]
        elif len(json_fields) == 1:
            args = [Q(data__has_key=json_fields[0])]
        else:
            args = []

        kw = {f'{field}__isnull': False for field in row_fields}
        queryset = filter_or(queryset, *args, **kw)

        # Order by time
        queryset = queryset.order_by('time')

        # Interval
        interval = params.get('interval')
        if interval:
            # XXX Interval and tags don't work together (TEST)
            # XXX Interval requires fields (TEST)
            interval = int(interval)
            queryset = queryset\
                .annotate(key=(F('time') / interval) * interval)\
                .values('key')

            interval_agg = params.get('interval_agg')
            if interval_agg:
                agg = {
                    'avg': Avg,
                    'count': Count,
                    'max': Max,
                    'min': Min,
                    'stddev': StdDev,
                    'sum': Sum,
                    'variance': Variance,
                }[interval_agg]

                annotations = {}
                for name in row_fields:
                    annotations[name] = agg(name)
                for name in json_fields:
                    field = KeyTextTransform(name, 'data') # Access: data->>'name'
                    field = Cast(field, FloatField()) # Cast
                    annotations[name] = agg(field)

                queryset = queryset.annotate(time=F('key'), **annotations)
            else:
                queryset = queryset.order_by('key', 'time').distinct('key')
                queryset = queryset.annotate(**{
                    name: KeyTextTransform(name, 'data')
                    for name in json_fields})
                queryset = queryset.values()

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
                row = {'time': obj.time}
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
        table = params.get('table')
        if table is None:
            raise serializers.ValidationError(detail="Missing 'table' query parameter")

        limit = params.get('limit')
        columns = params.getlist('fields')
        interval = params.get('interval')
        interval_agg = params.get('interval_agg')

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
                    where=f"database = '{settings.CLICKHOUSE_NAME}' AND table = '{table}'",
                    order_by='name',
                )
                columns = [name for name, in columns]

            # Remove TIMESTAMP
            columns = [f'"{name}"' for name in columns if name != 'TIMESTAMP']

            # Defaults
            group_by = None
            order_by = 'time'
            limit_by = None
            key = None

            # Average over interval
            if interval:
                if interval_agg:
                    time = [f'intDiv(TIMESTAMP, {interval}) * {interval} AS time']
                    columns = time + [f'{interval_agg}({x}) AS {x}' for x in columns]
                    group_by = 'time'
                else:
                    key = [f'intDiv(TIMESTAMP, {interval}) * {interval} AS key']
                    columns = key + ['TIMESTAMP AS time'] + columns
                    limit_by = (1, 'key')
            else:
                columns = ['TIMESTAMP AS time'] + columns

            # Get data
            rows, columns = clickhouse.select(
                table, columns=columns, where=where,
                group_by=group_by, order_by=order_by, limit_by=limit_by,
                limit=limit,
                with_column_types=True,
            )
            columns = [name for name, typ in columns]

            # Remove key
            if key:
                columns = columns[1:]
                rows = [row[1:] for row in rows]

        return Response({'columns': columns, 'rows': rows, 'format': 'compact'})
