# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import csv

from django.apps import apps
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from geoposition.fields import GeopositionField
from uuidfield import UUIDField
from easy_thumbnails.fields import ThumbnailerImageField
from pytz.exceptions import NonExistentTimeError
from django.utils import timezone
from dateutil import parser

from . import managers


class ValueFields(models.Model):
    value_fields = ('so2', 'no', 'no2', 'o3', 'ben', 'pm10_teom', 'pm10', 'pm25', 'ec', 'oc',
        'sti', 'stns', 'met', 'co', 'pm10_pb')

    class Meta:
        abstract = True

    @classmethod
    def get_verbose_names(cls, fields):
        return tuple([cls._meta.get_field(field).verbose_name for field in fields])


@python_2_unicode_compatible
class MeasuringPoint(ValueFields):
    EU_TYPING_CITY_BACKGROUND = 1
    EU_TYPING_CITY_TRAFFIC = 2
    EU_TYPING_SUBURBAN = 3
    EU_TYPING_RURAL_CLOSE_TO_CITY = 4
    EU_TYPING_RURAL = 5
    EU_TYPING_RURAL_BACKGROUND = 6
    EU_TYPING_HEIGHT_STATION = 7
    EU_TYPING_CHOICES = (
        (EU_TYPING_CITY_BACKGROUND, 'städtischer Hintergrund'),
        (EU_TYPING_CITY_TRAFFIC, 'städtisch/Verkehr'),
        (EU_TYPING_SUBURBAN, 'vorstädtisches Gebiet'),
        (EU_TYPING_RURAL_CLOSE_TO_CITY, 'ländlich, stadtnah'),
        (EU_TYPING_RURAL, 'ländlich'),
        (EU_TYPING_RURAL_BACKGROUND, 'ländlicher Hintergrund'),
        (EU_TYPING_HEIGHT_STATION, 'Höhenstation'),
    )
    CATEGORY_LOCAL = 1
    CATEGORY_CITY = 2
    CATEGORY_TRAFFIC = 3
    CATEGORIES = (
        (CATEGORY_LOCAL, 'Stationen zur Beurteilung der regionalen Vorbelastung'),
        (CATEGORY_CITY, 'Stationen zur Beurteilung der allgemeinen städtischen Belastung'),
        (CATEGORY_TRAFFIC, 'Stationen zur Beurteilung verkehrsnaher Belastungen'),
    )
    name = models.CharField('Name', max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    form_id = models.IntegerField('Formular ID', unique=True)
    location = models.CharField('Standort', max_length=100,
        help_text='Straße bzw. ungefähren Standort angeben')
    city = models.CharField('Stadt', max_length=100, help_text='Stadt oder Ortschaft angeben')
    amsl = models.IntegerField('Höhe über NN [m]', blank=True, null=True)
    eu_typing = models.IntegerField('Typisierung nach EU-Richtlinie', choices=EU_TYPING_CHOICES,
        default=EU_TYPING_CITY_BACKGROUND)
    category = models.IntegerField('Kategorie', choices=CATEGORIES, default=CATEGORY_CITY)
    image = ThumbnailerImageField('Bild', upload_to='measuring_stations', blank=True)
    position = GeopositionField()
    so2 = models.BooleanField('SO2', default=False)
    no = models.BooleanField('NO', default=False)
    no2 = models.BooleanField('NO2', default=False)
    o3 = models.BooleanField('O3', default=False)
    ben = models.BooleanField('BEN', default=False)
    pm10_teom = models.BooleanField('PM10TEOM', default=False)
    pm10 = models.BooleanField('PM10', default=False)
    pm25 = models.BooleanField('PM2.5', default=False)
    ec = models.BooleanField('EC', default=False)
    oc = models.BooleanField('OC', default=False)
    sti = models.BooleanField('STI', default=False)
    stns = models.BooleanField('STNS', default=False)
    met = models.BooleanField('MET', default=False)
    co = models.BooleanField('CO', default=False)
    pm10_pb = models.BooleanField('PM10 Pb', default=False)

    objects = managers.MeasuringPointManager()

    class Meta:
        verbose_name = 'Messstelle'
        verbose_name_plural = 'Messstellen'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('measuring_stations_measuringpoint_detail', kwargs={'slug': self.slug})

    def natural_key(self):
        return (self.name,)

    def get_csv(self, csvfile, limit, flat=False):
        writer = csv.writer(csvfile, lineterminator='\n')
        model = apps.get_model('measuring_stations', 'IndicatedValue')
        if flat:
            writer.writerow(("x", ""))
            names = model.get_verbose_names(self.active_values)
            values = self.indicated_values.values_list(*self.active_values)[:limit][0]
            writer.writerows(zip(names, values))
        else:
            csv_fields = ('date_created',) + self.active_values
            writer.writerow(model.get_verbose_names(csv_fields))
            writer.writerows(self.indicated_values.values_list(*csv_fields)[:limit])
        return csvfile

    def put_csv(self, content, unit, form_id, station_name):
        reader = csv.DictReader(content, delimiter=b';')
        print station_name
        try:
            station = MeasuringPoint.objects.get(form_id=form_id)
        except MeasuringPoint.DoesNotExist:
            self.stderr.write(u'MeasuringPoint "{0}"" not found'.format(station_name))
            return
        unit_key = unit.lower().replace('.', '')
        for row in reader:
            dateRow = row.get('Datum Zeit', '')
            if len(dateRow):
                try:
                    date = parser.parse(dateRow, dayfirst=True)
                    if timezone.is_naive(date):
                        try:
                            date = timezone.make_aware(date, self.tz)
                        except NonExistentTimeError as e:
                            self.stderr.write(str(e))
                except ValueError:
                    self.stderr.write('Failed to parse date "{0}"'.format(dateRow))
                    continue

                value = row[(' ' + station_name + ' ' + unit).encode('iso-8859-1')].strip()

                if value.find(',') > -1:
                    value = float(value.replace(',', '.'))
                is_float = isinstance(value, float)
                if is_float or (value.find('g/m') == -1 and value.find('n. def.') == -1):
                    IndicatedValue.objects.update_or_create(date_created=date,
                                measuring_point=station, defaults={unit_key: float(value)})

    @property
    def active_values(self):
        return tuple([field for field in self.value_fields if getattr(self, field)])

    def active_names(self):
        return ', '.join(self.get_verbose_names(self.active_values))
    active_names.short_description = 'Angezeigte Messwerte'


@python_2_unicode_compatible
class IndicatedValue(ValueFields):
    uuid = UUIDField(auto=True, primary_key=True)
    date_created = models.DateTimeField('Datum')
    measuring_point = models.ForeignKey(MeasuringPoint, related_name='indicated_values',
        verbose_name='Messstelle')
    so2 = models.FloatField('SO2', default=0)
    no = models.FloatField('NO', default=0)
    no2 = models.FloatField('NO2', default=0)
    o3 = models.FloatField('O3', default=0)
    ben = models.FloatField('BEN', default=0)
    pm10_teom = models.FloatField('PM10TEOM', default=0)
    pm10 = models.FloatField('PM10', default=0)
    pm25 = models.FloatField('PM2.5', default=0)
    ec = models.FloatField('EC', default=0)
    oc = models.FloatField('OC', default=0)
    sti = models.FloatField('STI', default=0)
    stns = models.FloatField('STNS', default=0)
    met = models.FloatField('MET', default=0)
    co = models.FloatField('CO', default=0)
    pm10_pb = models.FloatField('PM10 Pb', default=0)

    class Meta:
        verbose_name = 'Messwert'
        verbose_name_plural = 'Messwerte'
        ordering = ['-date_created']
        unique_together = ('date_created', 'measuring_point')

    def __str__(self):
        return '%s %s' % (self.date_created, self.measuring_point)
