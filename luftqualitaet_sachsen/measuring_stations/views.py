from django.views.generic import DetailView
from django.shortcuts import render

from .models import MeasuringPoint


def overview(request):
    ctx = {'measuring_points': MeasuringPoint.objects.all()}
    return render(request, 'measuring_stations/overview.html', ctx)


class MeasuringPointDetailView(DetailView):
    model = MeasuringPoint
