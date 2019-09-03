# Django
from django.db.models import F, Func, Min, Q

# Rest framework
from rest_framework import generics
from rest_framework import pagination
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import serializers

# App
from .clickhouse import ClickHouse
from .models import Metadata, Frame


#
# Query v2
#
class Query2Serializer(serializers.ModelSerializer):
    class Meta:
        model = Frame
        fields = ['time']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        params = self.context['request'].query_params

        # Fields
        fields = params.getlist('fields')
        if fields:
            for field in fields:
                value = getattr(instance, field, None)
                if value is None and instance.data:
                    value = instance.data.get(field)
                if value is not None:
                    data[field] = value
        else:
            for field in instance.get_data_fields():
                value = getattr(instance, field, None)
                if value is not None:
                    data[field] = value
            if instance.data:
                data.update(instance.data)

        # Tags
        tags = params.getlist('tags')
        if tags:
            metadata = instance.metadata
            for tag in tags:
                value = metadata.tags.get(tag)
                if value is not None:
                    data[tag] = value

        return data


class Query2Pagination(pagination.CursorPagination):
    ordering = ['time']
    page_size_query_param = 'limit'


class Epoch(Func):
   function = 'EXTRACT'
   template = "%(function)s('epoch' from %(expressions)s)"


class Query2View(generics.ListAPIView):
    serializer_class = Query2Serializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = Query2Pagination


    def list(self, request, *args, **kwargs):
        params = self.request.query_params
        table = params.get('table')
        if table is not None:
            data = self.get_clickhouse(table, params)
            return Response(data)

        return super().list(request, *args, **kwargs)


    def get_clickhouse(self, table, params):
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
            results = [dict(zip(columns, row)) for row in rows]

        return [{'previous': None, 'next': None, 'results': results}]


    def get_queryset(self):
        params = self.request.query_params

        # Metadatas
        # TODO Optimize using data__contains when key does not end by __gte/__lte
        # because __contains will trigger usage of the GIN index.
        kw = {}
        exclude = {'format', 'limit', 'fields', 'tags', 'interval', 'time__gte', 'time__lte'}
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

        # Interval
        interval = params.get('interval')
        if interval:
            subquery = queryset\
                .order_by()\
                .annotate(key=F('time') / int(interval))\
                .values('key')\
                .annotate(t=Min('time'))\
                .values('t')

            queryset = queryset.filter(time__in=subquery)

        tags = params.getlist('tags')
        return queryset.select_related('metadata') if tags else queryset
