from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.db.models import Max
from django import forms
from django.utils.functional import cached_property
from django.views.generic import FormView

from bokeh.plotting import figure
from bokeh.embed import components

from .models import Frame, Metadata


def name_choices():
    return Metadata.objects.values_list('name', 'name').distinct().order_by('name')

def field_choices():
    return ((x, x) for x in Frame.get_data_fields())

class ExploreForm(forms.Form):
    name = forms.ChoiceField(choices=name_choices, required=False)
    field = forms.ChoiceField(choices=field_choices, required=False)
    days = forms.IntegerField(required=False, initial=2, min_value=1)


class ExploreView(FormView):
    template_name = 'wsn/explore.html'
    form_class = ExploreForm

    @cached_property
    def form(self):
        return self.form_class(self.request.GET or None)

    @cached_property
    def name(self):
        if self.form.is_valid():
            return self.form.cleaned_data.get('name')
        return None

    @cached_property
    def field(self):
        if self.form.is_valid():
            return self.form.cleaned_data.get('field')
        return None

    @cached_property
    def days(self):
        if self.form.is_valid():
            return self.form.cleaned_data.get('days')
        return None

    @cached_property
    def show_plot(self):
        return self.name and self.field and self.days

    @cached_property
    def frames(self):
        name = self.name
        field = self.field
        days = self.days

        # Filter frames by name
        frames = Frame.objects.filter(metadata__name=name)

        # Exclude frames without value
        if field in Frame.get_data_fields():
            frames = frames.exclude(**{field: None})
            field_key = field
        else:
            frames = frames.filter(data__haskey=field)
            field_key = f'data__{field}'

        # Filter by date
        until = frames.aggregate(time=Max('time'))['time']
        since = until - days * 24 * 3600
        frames = frames.filter(time__gte=since).order_by('time')
        self.since = datetime.utcfromtimestamp(since)
        self.until = datetime.utcfromtimestamp(since)

        # Return
        return frames.values_list('time', field_key)

    @cached_property
    def frames_count(self):
        return self.frames.count()

    @cached_property
    def components(self):
        x = []
        y = []
        for value in self.frames:
            x.append(datetime.utcfromtimestamp(value[0]))
            y.append(value[1])

        plot = figure(
            title=self.name,
            x_axis_label='Time', x_axis_type='datetime',
            plot_width=800,
            plot_height=400,
        )
        plot.line(x, y, legend=self.field, line_width=2)
        return components(plot)

    @cached_property
    def script(self):
        return self.components[0]

    @cached_property
    def div(self):
        return self.components[1]


explore = login_required(ExploreView.as_view())
