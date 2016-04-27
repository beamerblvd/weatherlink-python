from __future__ import absolute_import

import contextlib
import decimal
import datetime

import mysql.connector
import pytz

import weatherlink.utils

"""
This module includes an exporter that can take WeatherLink records imported or downloaded and export them to a MySQL
database. Though the schema used can be customized, the schema in mysql.sql is recommended. Additionally, this exporter
can be used to calculate daily, weekly, monthly, yearly, and all-time summaries, and to analyze rain events.
"""

COLUMN_MAP_DO_NOT_INSERT = '__do_not_insert_this_value__'

THREE_HOURS_IN_SECONDS = 10800
ZERO = decimal.Decimal('0.0')
TENTHS = decimal.Decimal('0.01')


class MySQLExporter(object):
	DEFAULT_ARCHIVE_TABLE_NAME = 'weather_archive_record'
	DEFAULT_ARCHIVE_TABLE_COLUMN_MAP = {
		'timestamp': 'timestamp_weatherlink',
	    'date': 'timestamp_station',
	    'timestamp_utc': 'timestamp_utc',
	    'summary_year': 'summary_year',
	    'summary_month': 'summary_month',
	    'summary_day': 'summary_day',
	    # averages and end-of-period values of actual, physical measurements
	    'temperature_outside': 'temperature_outside',
	    'temperature_outside_low': 'temperature_outside_low',
	    'temperature_outside_high': 'temperature_outside_high',
	    'temperature_inside': 'temperature_inside',
	    'humidity_outside': 'humidity_outside',
	    'humidity_inside': 'humidity_inside',
	    'barometric_pressure': 'barometric_pressure',
	    'wind_speed': 'wind_speed',
	    'wind_direction_prevailing': 'wind_speed_direction',
	    'wind_speed_high': 'wind_speed_high',
	    'wind_direction_speed_high': 'wind_speed_high_direction',
	    'wind_run_distance_total': 'wind_run_distance_total',
	    'rain_amount': 'rain_total',
	    'rain_rate': 'rain_rate_high',
	    'rain_amount_clicks': 'rain_clicks',
	    'rain_rate_clicks': 'rain_click_rate_high',
	    'solar_radiation': 'solar_radiation',
	    'solar_radiation_high': 'solar_radiation_high',
	    'uv_index': 'uv_index',
	    'uv_index_high': 'uv_index_high',
	    'evapotranspiration': 'evapotranspiration',
	    # calculated values derived from two or more physical measurements
	    'temperature_wet_bulb': 'temperature_wet_bulb',
	    'temperature_wet_bulb_low': 'temperature_wet_bulb_low',
	    'temperature_wet_bulb_high': 'temperature_wet_bulb_high',
	    'dew_point_outside': 'dew_point_outside',
	    'dew_point_outside_low': 'dew_point_outside_low',
	    'dew_point_outside_high': 'dew_point_outside_high',
	    'dew_point_inside': 'dew_point_inside',
	    'heat_index_outside': 'heat_index_outside',
	    'heat_index_outside_low': 'heat_index_outside_low',
	    'heat_index_outside_high': 'heat_index_outside_high',
	    'heat_index_inside': 'heat_index_inside',
	    'wind_chill': 'wind_chill',
	    'wind_chill_low': 'wind_chill_low',
	    'wind_chill_high': 'wind_chill_high',
	    'thw_index': 'thw_index',
	    'thw_index_low': 'thw_index_low',
	    'thw_index_high': 'thw_index_high',
	    'thsw_index': 'thsw_index',
	    'thsw_index_low': 'thsw_index_low',
	    'thsw_index_high': 'thsw_index_high',
	}

	ARCHIVE_ATTRIBUTES_TO_COPY = frozenset({
		'timestamp',
		'date',
		'temperature_outside',
	    'temperature_outside_low',
	    'temperature_outside_high',
	    'temperature_inside',
	    'humidity_outside',
	    'humidity_inside',
	    'barometric_pressure',
	    'wind_speed',
	    'wind_direction_prevailing',
	    'wind_speed_high',
	    'wind_direction_speed_high',
	    'rain_amount',
	    'rain_rate',
	    'rain_amount_clicks',
	    'rain_rate_clicks',
	    'solar_radiation',
	    'solar_radiation_high',
	    'uv_index',
	    'uv_index_high',
	    'evapotranspiration',
	})

	DEFAULT_TIME_ZONE = pytz.timezone('America/Chicago')

	def __init__(self, username, password, database, host='127.0.0.1', port=3306):
		self.username = username
		self.password = password
		self.database = database
		self.host = host
		self.port = port

		self._archive_table_name = self.DEFAULT_ARCHIVE_TABLE_NAME
		self._archive_table_column_map = self.DEFAULT_ARCHIVE_TABLE_COLUMN_MAP
		self._station_time_zone = self.DEFAULT_TIME_ZONE
		self._record_minute_span = 30

		self._connection = None

	@property
	def archive_table_name(self):
		return self._archive_table_name or self.DEFAULT_ARCHIVE_TABLE_NAME

	@archive_table_name.setter
	def archive_table_name(self, value):
		self._archive_table_name = value

	@property
	def archive_table_column_map(self):
		return self._archive_table_column_map or self.DEFAULT_ARCHIVE_TABLE_COLUMN_MAP

	@archive_table_column_map.setter
	def archive_table_column_map(self, value):
		self._archive_table_column_map = value

	@property
	def station_time_zone(self):
		return self._station_time_zone or self.DEFAULT_TIME_ZONE

	@station_time_zone.setter
	def station_time_zone(self, value):
		self._station_time_zone = pytz.timezone(value) if isinstance(value, basestring) else value

	@property
	def record_minute_span(self):
		return self._record_minute_span or 30

	@record_minute_span.setter
	def record_minute_span(self, value):
		self._record_minute_span = value

	def connect(self):
		self._connection = mysql.connector.connect(
			host=self.host,
			port=self.port,
			database=self.database,
			user=self.username,
			password=self.password,
		)

	def disconnect(self):
		if self._connection:
			try:
				self._connection.close()
			finally:
				self._connection = None

	def __enter__(self):
		self.connect()

	def __exit__(self, exception_type, exception_value, exception_traceback):
		try:
			self.disconnect()
		except:
			# Only allow this exception to be raised if an exception did not triger the context manager exit
			if not exception_type:
				raise

	@contextlib.contextmanager
	def _get_cursor(self, statement, arguments):
		cursor = None
		try:
			cursor = self._connection.cursor()
			cursor.execute(statement, arguments)
			yield cursor
		finally:
			if cursor:
				try:
					cursor.close()
				except:
					pass

	def export_record(self, record):
		argument_map = {}
		self._add_timestamp_values_to_arguments(record, argument_map)
		self._add_physical_values_to_arguments(record, argument_map)
		self._add_calculated_values_to_arguments(record, argument_map)

		column_list = []
		arguments = []
		for k, v in argument_map.iteritems():
			if k != COLUMN_MAP_DO_NOT_INSERT:
				column_list.append(k)
				arguments.append(v)

		statement = (
			'INSERT INTO ' + self.archive_table_name + ' (' + ', '.join(column_list) + ') ' +
			'VALUES (' + ', '.join(['%s'] * len(column_list)) + ');'
		)

		with self._get_cursor(statement, arguments) as cursor:
			self._connection.commit()

	def _add_timestamp_values_to_arguments(self, record, arguments):
		column_map = self.archive_table_column_map

		d = record.date.replace(tzinfo=self.station_time_zone).astimezone(pytz.UTC).replace(tzinfo=None)
		arguments[column_map['timestamp_utc']] = d
		arguments[column_map['summary_year']] = record.date.year
		arguments[column_map['summary_month']] = record.date.month
		arguments[column_map['summary_day']] = record.date.day

		# week_year = d.isocalendar()[0]
		# week_number = d.isocalendar()[1]
		# week_day = d.weekday()
		# week_start = (d - datetime.timedelta(days=week_day)).replace(hour=0, minute=0, second=0)
		# week_end = (week_start + datetime.timedelta(days=6)).replace(hour=23, minute=59, second=59)

	def _add_physical_values_to_arguments(self, record, arguments):
		column_map = self.archive_table_column_map

		for attribute in self.ARCHIVE_ATTRIBUTES_TO_COPY:
			if attribute in record:
				arguments[column_map[attribute]] = record[attribute]

	def _add_calculated_values_to_arguments(self, record, arguments):
		column_map = self.archive_table_column_map

		for k, v in weatherlink.utils.calculate_all_record_values(record, self.record_minute_span).iteritems():
			if k in column_map:
				arguments[column_map[k]] = v

	def recalculate_summaries_for_date(self, date):
		pass

	def _recalculate_daily_summary(self, date):
		pass

	def _recalculate_monthly_summary(self):
		pass

	def _recalculate_yearly_summary(self):
		pass

	def _recalculate_all_time_summary(self):
		pass

	def find_new_rain_events(self):
		while True:
			with self._get_cursor('SELECT max(timestamp_end) FROM weather_rain_event;', []) as cursor:
				latest = cursor.fetchone()[0]

				if latest:
					query = (
						'SELECT timestamp_station, rain_total, rain_rate_high FROM weather_archive_record '
						'WHERE timestamp_station > %s AND rain_total > 0 ORDER BY timestamp_station LIMIT 1;'
					)
					cursor.execute(query, [latest])
				else:
					query = (
						'SELECT timestamp_station, rain_total, rain_rate_high FROM weather_archive_record '
						'WHERE timestamp_station IS NOT NULL AND rain_total > 0 ORDER BY timestamp_station LIMIT 1;'
					)
					cursor.execute(query, [])

				start_record = cursor.fetchone()
				if not start_record:
					# There are no more rain events. We're done.
					break

				# This is the start of a new rain event
				last_rain = start_record[0]
				event_total_rain = start_record[1]
				event_rain_rates = [start_record[2]]
				event_max_rain_rate = event_rain_rates[0]
				event_max_rate_time = last_rain
				cursor.execute(
					'SELECT timestamp_station, rain_total, rain_rate_high FROM weather_archive_record '
					'WHERE timestamp_station > %s ORDER BY timestamp_station;',
					[start_record[0]],
				)
				for (timestamp_station, rain_total, rain_rate_high) in cursor:
					if (timestamp_station - last_rain).seconds > THREE_HOURS_IN_SECONDS:
						break

					if rain_total == 0:
						continue

					last_rain = timestamp_station
					event_total_rain += rain_total
					event_rain_rates.append(rain_rate_high)
					old = event_max_rain_rate
					event_max_rain_rate = max(event_max_rain_rate, rain_rate_high)
					if old != event_max_rain_rate:
						event_max_rate_time = timestamp_station

				cursor.fetchall()  # Fetch remaining rows to prevent an error

				if (datetime.datetime.now(self.station_time_zone) - last_rain) < THREE_HOURS_IN_SECONDS:
					# This is an ongoing rain event, so don't record it yet. We're done.
					break

				average_rate = (sum(event_rain_rates) / len(event_rain_rates)).quantize(TENTHS)

				cursor.execute(
					'INSERT INTO weather_rain_event (timestamp_start, timestamp_end, timestamp_rain_rate_high, '
					'rain_total, rain_rate_average, rain_rate_high) VALUES (%s, %s, %s, %s, %s, %s);',
					[start_record[0], last_rain, event_max_rate_time, event_total_rain, average_rate, event_max_rain_rate],
				)
				self._connection.commit()


	def get_newest_timestamp(self):
		with self._get_cursor('SELECT max(timestamp_weatherlink) FROM weather_archive_record;', []) as cursor:
			return cursor.fetchone()[0]
