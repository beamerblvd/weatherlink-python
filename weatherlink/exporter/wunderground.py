"""
This module contains an exporter for uploading weather data to the Weather Underground PWS Network.
"""

from __future__ import absolute_import

import collections
# noinspection PyUnresolvedReferences
from six.moves.urllib.parse import quote as url_quote

import pytz
import requests
import six

import weatherlink.utils


def _get_wind_gust(exporter, *_):
	i = 0
	gust = None
	gust_direction = None

	for record in exporter.record_queue:
		if i > 24:  # 1 minute
			break
		i += 1

		if record['wind_speed'] is not None:
			old_gust = gust
			gust = max(gust, record['wind_speed'])
			if gust != old_gust:
				gust_direction = record['wind_direction_degrees']

	return gust, gust_direction


def _get_2_minute_average_wind_direction(exporter, *_):
	i = 0
	current_direction_list = []

	for record in exporter.record_queue:
		if i > 48:  # 2 minutes
			break
		i += 1

		if record['wind_direction_degrees'] is not None:
			current_direction_list.append(record['wind_direction_degrees'])

	return (sum(current_direction_list) / len(current_direction_list)) if current_direction_list else None


class WundergroundExporter(object):
	URL_SIMPLE_UPDATE = (
		'http://weatherstation.wunderground.com/weatherstation/updateweatherstation.php?'
		'action=updateraw&softwaretype=WeatherLink'
	)

	URL_RAPID_UPDATE = (
		'http://rtupdate.wunderground.com/weatherstation/updateweatherstation.php?'
		'action=updateraw&softwaretype=WeatherLink'
	)

	ATTRIBUTE_MAP_SIMPLE_UPDATE = (
		('windspeedmph', 'wind_speed', ),
		('winddir', 'wind_direction_prevailing_degrees', ),
		('windgustmph', 'wind_speed_high', ),
		('windgustdir', 'wind_direction_speed_high_degrees', ),
		('humidity', 'humidity_outside', ),
		('tempf', 'temperature_outside', ),
		('baromin', 'barometric_pressure', ),
		('solarradiation', 'solar_radiation', ),
		('UV', 'uv_index', ),
		('indoortempf', 'temperature_inside', ),
		('indoorhumidity', 'humidity_inside', ),
	)

	ATTRIBUTE_CALCULATIONS_SIMPLE_UPDATE = (
		('windspdmph_avg2m', None, ),  # TODO
		('winddir_avg2m', None, ),  # TODO
		('windgustmph_10m', None, ),  # TODO
		('windgustdir_10m', None, ),  # TODO
		(
			'dewptf',
			lambda e, r: weatherlink.utils.calculate_dew_point(r['temperature_outside'], r['humidity_outside']),
		),
		('rainin', None, ),  # TODO rain last hour
		('dailyrainin', None, ),  # TODO rain today
	)

	ATTRIBUTE_MAP_RAPID_UPDATE = (
		('windspeedmph', 'wind_speed', ),
		('winddir', 'wind_direction_degrees', ),
		('windgustmph', 'wind_gust', ),
		('windgustdir', 'wind_gust_direction', ),
		('windspdmph_avg2m', 'wind_speed_2_minute_average', ),
		('windgustmph_10m', 'wind_speed_10_minute_gust', ),
		('windgustdir_10m', 'wind_speed_10_minute_gust_direction_degrees', ),
		('humidity', 'humidity_outside', ),
		('dewptf', 'dew_point', ),
		('tempf', 'temperature_outside', ),
		('rainin', 'rain_amount_1_hour', ),  # rain last hour
		('dailyrainin', 'rain_amount_today', ),  # rain today
		('baromin', 'barometric_pressure', ),
		('solarradiation', 'solar_radiation', ),
		('UV', 'uv_index', ),
		('indoortempf', 'temperature_inside', ),
		('indoorhumidity', 'humidity_inside', ),
	)

	ATTRIBUTE_CALCULATIONS_RAPID_UPDATE = (
		('winddir_avg2m', _get_2_minute_average_wind_direction, ),
	)

	DEFAULT_TIME_ZONE = pytz.timezone('America/Chicago')

	def __init__(self, station_id, password):
		self.station_id = station_id
		self.password = password

		self._station_time_zone = self.DEFAULT_TIME_ZONE
		self._session = requests.Session()

		self.record_queue = collections.deque(maxlen=50)  # 34560 is a whole day, 50 is 2 minutes

	@property
	def station_time_zone(self):
		return self._station_time_zone or self.DEFAULT_TIME_ZONE

	@station_time_zone.setter
	def station_time_zone(self, value):
		self._station_time_zone = pytz.timezone(value) if isinstance(value, six.string_types) else value

	def _send_update(self, url, attribute_map, attribute_calculations, record):
		d = record.date.replace(tzinfo=self.station_time_zone).astimezone(pytz.UTC).replace(tzinfo=None)

		url = '%s&ID=%s&PASSWORD=%s&dateutc=%s' % (
			url,
			self.station_id,
			url_quote(self.password, safe=''),
			url_quote(d.strftime('%Y-%m-%d %H:%M:%S'), safe=''),
		)

		for parameter, field in attribute_map or []:
			if field and record[field] is not None:
				url += '&%s=%s' % (parameter, url_quote(record[field], safe=''), )

		for parameter, function in attribute_calculations or []:
			if function:
				value = function(self, record)
				if value is not None:
					url += '&%s=%s' % (parameter, url_quote(value, safe=''), )

		response = self._session.get(url)

		assert 200 <= response.status_code < 300, 'Status code %s unexpected' % response.status_code

		assert response.text == 'success', 'Response "%s" unexpected' % response.text

	def send_simple_update(self, record):
		self.record_queue.appendleft(record)

		self._send_update(
			self.URL_SIMPLE_UPDATE,
			self.ATTRIBUTE_MAP_SIMPLE_UPDATE,
			self.ATTRIBUTE_CALCULATIONS_SIMPLE_UPDATE,
			record,
		)

	def send_rapid_update(self, record):
		self.record_queue.appendleft(record)

		record['wind_gust'], record['wind_gust_direction'] = _get_wind_gust(self, record)

		self._send_update(
			self.URL_RAPID_UPDATE,
			self.ATTRIBUTE_MAP_RAPID_UPDATE,
			self.ATTRIBUTE_CALCULATIONS_RAPID_UPDATE,
			record,
		)
