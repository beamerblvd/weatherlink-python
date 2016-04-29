from __future__ import absolute_import

import contextlib
import decimal
import datetime

import mysql.connector
import mysql.connector.errors
import pytz

import weatherlink.utils

"""
This module includes an exporter that can take WeatherLink records imported or downloaded and export them to a MySQL
database. Though the schema used can be customized, the schema in mysql.sql is recommended. Additionally, this exporter
can be used to calculate daily, weekly, monthly, yearly, and all-time summaries, and to analyze rain events.
"""

COLUMN_MAP_DO_NOT_INSERT = '__do_not_insert_this_value__'

THREE_HOURS_IN_SECONDS = 10800
HUNDREDTHS = decimal.Decimal('0.01')


class MySQLExporter(object):
	DEFAULT_ARCHIVE_TABLE_NAME = 'weather_archive_record'
	DEFAULT_ARCHIVE_TABLE_COLUMN_MAP = {
		'timestamp': 'timestamp_weatherlink',
	    'date': 'timestamp_station',
	    'timestamp_utc': 'timestamp_utc',
	    'minutes_covered': 'minutes_covered',
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
		'minutes_covered',
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
	def _get_cursor(self, statement=None, arguments=None):
		cursor = None
		try:
			cursor = self._connection.cursor()
			if statement:
				if arguments:
					cursor.execute(statement, arguments)
				else:
					cursor.execute(statement)
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

	def _add_physical_values_to_arguments(self, record, arguments):
		column_map = self.archive_table_column_map

		for attribute in self.ARCHIVE_ATTRIBUTES_TO_COPY:
			if attribute in record:
				arguments[column_map[attribute]] = record[attribute]

	def _add_calculated_values_to_arguments(self, record, arguments):
		column_map = self.archive_table_column_map

		for k, v in weatherlink.utils.calculate_all_record_values(record).iteritems():
			if k in column_map:
				arguments[column_map[k]] = v

	def recalculate_summaries_for_dates(self, dates):
		# We create a set of everything that needs recalculating so that we don't do any duplicate work
		y = set()
		ym = set()
		ymd = set()
		yw = set()
		ywdd = []

		for date in dates:
			year, month, day = date.year, date.month, date.day
			if (year, month, day, ) in ymd:
				continue

			self._recalculate_daily_summary(year, month, day)

			y.add(year)
			ym.add((year, month, ))
			ymd.add((year, month, day, ))

			week_year, week_number, _ = date.isocalendar()
			if (week_year, week_number, ) in yw:
				continue

			yw.add((week_year, week_number, ))
			ywdd.append((week_year, week_number, date, ))

		y = sorted(list(y))
		ym = sorted(list(ym))

		for args in ywdd:
			self._recalculate_weekly_summary(*args)

		for args in ym:
			self._recalculate_monthly_summary(*args)

		for year in y:
			self._recalculate_yearly_summary(year)

		self._recalculate_all_time_summary()

	def _recalculate_daily_summary(self, year, month, day):
		with self._get_cursor() as cursor:
			summary_id, average_temperature = self._recalculate_summary_from_arguments(
				cursor,
				'summary_year = %s AND summary_month = %s AND summary_day = %s',
				[year, month, day],
				'DAILY',
				year,
				month,
				0,
				day,
			)

			query = (
				'SELECT wind_speed, wind_speed_direction, timestamp_station, minutes_covered '
				'FROM weather_archive_record WHERE summary_year = %s AND summary_month = %s AND summary_day = %s '
				'ORDER BY timestamp_station;'
			)
			cursor.execute(query, [year, month, day])
			wsh10ma, wsh10mad, wsh10mas, wsh10mae = weatherlink.utils.calculate_10_minute_wind_average(cursor)

			if wsh10mas:
				# The date represents the end of the record time span, so change it to the beginning for the start time
				# We use one minute here instead of minutes_covered because the util function has already reduced all
				# the records to one-minute records.
				wsh10mas = wsh10mas - datetime.timedelta(minutes=1)
			if wsh10mae:
				# We only need the time for the end, not the whole date, since the date part is the same as the start
				wsh10mae = wsh10mae.time()

			# Calculate degree days
			hdd = weatherlink.utils.calculate_heating_degree_days(average_temperature)
			cdd = weatherlink.utils.calculate_cooling_degree_days(average_temperature)

			# Update the summary with these daily-only expensive calculations
			cursor.execute(
				'UPDATE weather_calculated_summary SET '
				'integrated_heating_degree_days = %s, integrated_cooling_degree_days = %s, '
				'wind_speed_high_10_minute_average = %s, wind_speed_high_10_minute_average_direction = %s, '
				'wind_speed_high_10_minute_average_start = %s, wind_speed_high_10_minute_average_end = %s '
				'WHERE summary_id = %s;',
				[hdd, cdd, wsh10ma, wsh10mad, wsh10mas, wsh10mae, summary_id]
			)

			self._connection.commit()

	def _recalculate_weekly_summary(self, week_year, week_number, date):
		week_day = date.weekday()
		week_start = (date - datetime.timedelta(days=week_day)).replace(hour=0, minute=0, second=0)
		week_end = (week_start + datetime.timedelta(days=6)).replace(hour=23, minute=59, second=59)

		with self._get_cursor() as cursor:
			summary_id, _ = self._recalculate_summary_from_arguments(
				cursor,
				'timestamp_station >= %s AND timestamp_station <= %s',
				[week_start, week_end],
				'WEEKLY',
				week_year,
				0,
				week_number,
				0,
				week_start.date(),
				week_end.date(),
			)

			if week_start.year != week_end.year:
				where_clause = (
					"summary_type = 'DAILY' AND ( "
						'(summary_year = %s AND summary_month = %s AND summary_day >= %s) OR '
						'(summary_year = %s AND summary_month = %s AND summary_day <= %s)'
					' )'
				)
				where_arguments = [
					week_start.year, week_start.month, week_start.day, week_end.year, week_end.month, week_end.day
				]
			elif week_start.month != week_end.month:
				where_clause = (
					"summary_type = 'DAILY' AND summary_year = %s AND ( "
						'(summary_month = %s AND summary_day >= %s) OR (summary_month = %s AND summary_day <= %s)'
					' )'
				)
				where_arguments = [week_start.year, week_start.month, week_start.day, week_end.month, week_end.day]
			else:
				where_clause = (
					"summary_type = 'DAILY' AND summary_year = %s AND summary_month = %s AND "
					'summary_day >= %s AND summary_day <= %s'
				)
				where_arguments = [week_start.year, week_start.month, week_start.day, week_end.day]

			self._aggregate_degree_days_and_wind_averages(cursor, summary_id, where_clause, where_arguments)

			self._aggregate_average_wind_run_distance(cursor, summary_id, 'daily', where_clause, where_arguments)

			self._connection.commit()

	def _recalculate_monthly_summary(self, year, month):
		with self._get_cursor() as cursor:
			summary_id, _ = self._recalculate_summary_from_arguments(
				cursor,
				'summary_year = %s AND summary_month = %s',
				[year, month],
				'MONTHLY',
				year,
				month,
				0,
				0,
			)

			where_clause = "summary_type = 'DAILY' AND summary_year = %s AND summary_month = %s"
			where_arguments = [year, month]

			self._aggregate_degree_days_and_wind_averages(cursor, summary_id, where_clause, where_arguments)

			self._aggregate_average_wind_run_distance(cursor, summary_id, 'daily', where_clause, where_arguments)

			self._connection.commit()

	def _recalculate_yearly_summary(self, year):
		with self._get_cursor() as cursor:
			summary_id, _ = self._recalculate_summary_from_arguments(
				cursor,
				'summary_year = %s',
				[year],
				'YEARLY',
				year,
				0,
				0,
				0,
			)

			where_clause = "summary_type = 'MONTHLY' AND summary_year = %s"
			where_arguments = [year]

			self._aggregate_degree_days_and_wind_averages(cursor, summary_id, where_clause, where_arguments)

			self._aggregate_average_wind_run_distance(
				cursor,
				summary_id,
				'daily',
				"summary_type = 'DAILY' AND summary_year = %s",
				where_arguments,
			)
			self._aggregate_average_wind_run_distance(
				cursor,
				summary_id,
				'weekly',
				"summary_type = 'WEEKLY' AND summary_year = %s",
				where_arguments,
			)
			self._aggregate_average_wind_run_distance(cursor, summary_id, 'monthly', where_clause, where_arguments)

			self._connection.commit()

	def _recalculate_all_time_summary(self):
		pass

	def _recalculate_summary_from_arguments(
		self, cursor, where_clause, where_arguments, summary_type, year, month, week, day,
		week_start=None, week_end=None,
	):
		# Get most statistics in simple, optimized query
		query = (
			'SELECT min(temperature_outside_low), max(temperature_outside_high), avg(temperature_outside), '
			'min(temperature_inside), max(temperature_inside), avg(temperature_inside), '
			'min(humidity_outside), max(humidity_outside), avg(humidity_outside), '
			'min(humidity_inside), max(humidity_inside), avg(humidity_inside), '
			'min(barometric_pressure), max(barometric_pressure), avg(barometric_pressure), '
			'max(wind_speed_high), avg(wind_speed), sum(wind_run_distance_total), '
			'sum(rain_total), max(rain_rate_high), '
			'min(solar_radiation), max(solar_radiation_high), avg(solar_radiation), '
			'min(uv_index), max(uv_index_high), avg(uv_index), '
			'sum(evapotranspiration), '
			'min(temperature_wet_bulb_low), max(temperature_wet_bulb_high), avg(temperature_wet_bulb), '
			'min(dew_point_outside_low), max(dew_point_outside_high), avg(dew_point_outside), '
			'min(dew_point_inside), max(dew_point_inside), avg(dew_point_inside), '
			'min(heat_index_outside_low), max(heat_index_outside_high), avg(heat_index_outside), '
			'min(heat_index_inside), max(heat_index_inside), avg(heat_index_inside), '
			'min(wind_chill_low), max(wind_chill_high), avg(wind_chill), '
			'min(thw_index_low), max(thw_index_high), avg(thw_index), '
			'min(thsw_index_low), max(thsw_index_high), avg(thsw_index) '
			'FROM weather_archive_record WHERE ' + where_clause + ';'
		)
		cursor.execute(query, where_arguments)
		summary_values = cursor.fetchone()

		average_temperature = summary_values[2]
		wind_speed_high = summary_values[15]

		wind_direction_prevailing = wind_speed_high_direction = None
		if wind_speed_high:
			# Get statistical mode wind speed direction in more complex, expensive query
			query = (
				'SELECT wind_speed_direction FROM weather_archive_record WHERE ' + where_clause +
				' AND wind_speed_direction IS NOT NULL GROUP BY wind_speed_direction ORDER BY count(1) DESC LIMIT 1;'
			)
			cursor.execute(query, where_arguments)
			result = cursor.fetchone()
			if result:
				wind_direction_prevailing = result[0]

			# Get statistical mode wind speed direction restricted to the speed record for the summary period
			query = (
				'SELECT wind_speed_high_direction FROM weather_archive_record WHERE ' + where_clause +
				' AND wind_speed_high = %s AND wind_speed_high_direction IS NOT NULL '
				'GROUP BY wind_speed_high_direction ORDER BY count(1) DESC LIMIT 1;'
			)
			cursor.execute(query, where_arguments + [wind_speed_high])
			result = cursor.fetchone()
			if result:
				wind_speed_high_direction = result[0]

		# Find the existing summary, if there is one
		query = (
			'SELECT summary_id FROM weather_calculated_summary WHERE summary_type = %s AND summary_year = %s '
			'AND summary_month = %s AND summary_week = %s AND summary_day = %s;'
		)
		cursor.execute(query, [summary_type, year, month, week, day])
		summary = cursor.fetchone()

		if summary:
			summary_id = summary[0]
		else:
			# Insert an empty summary to reduce complexity
			query = (
				'INSERT INTO weather_calculated_summary '
				'(summary_type, summary_year, summary_month, summary_week, summary_day, week_start, week_end) '
				'VALUES (%s, %s, %s, %s, %s, %s, %s);'
			)
			cursor.execute(query, [summary_type, year, month, week, day, week_start, week_end])
			summary_id = cursor.lastrowid

		# Update the summary with our findings
		query = (
			'UPDATE weather_calculated_summary SET '
			'temperature_outside_low = %s, temperature_outside_high = %s, temperature_outside_average = %s, '
			'temperature_inside_low = %s, temperature_inside_high = %s, temperature_inside_average = %s, '
			'humidity_outside_low = %s, humidity_outside_high = %s, humidity_outside_average = %s, '
			'humidity_inside_low = %s, humidity_inside_high = %s, humidity_inside_average = %s, '
			'barometric_pressure_low = %s, barometric_pressure_high = %s, barometric_pressure_average = %s, '
			'wind_speed_high = %s, wind_speed_average = %s, wind_run_distance_total = %s, '
			'rain_total = %s, rain_rate_high = %s, '
			'solar_radiation_low = %s, solar_radiation_high = %s, solar_radiation_average = %s, '
			'uv_index_low = %s, uv_index_high = %s, uv_index_average = %s, '
			'evapotranspiration = %s, '
			'temperature_wet_bulb_low = %s, temperature_wet_bulb_high = %s, temperature_wet_bulb_average = %s, '
			'dew_point_outside_low = %s, dew_point_outside_high = %s, dew_point_outside_average = %s, '
			'dew_point_inside_low = %s, dew_point_inside_high = %s, dew_point_inside_average = %s, '
			'heat_index_outside_low = %s, heat_index_outside_high = %s, heat_index_outside_average = %s, '
			'heat_index_inside_low = %s, heat_index_inside_high = %s, heat_index_inside_average = %s, '
			'wind_chill_low = %s, wind_chill_high = %s, wind_chill_average = %s, '
			'thw_index_low = %s, thw_index_high = %s, thw_index_average = %s, '
			'thsw_index_low = %s, thsw_index_high = %s, thsw_index_average = %s, '
			'wind_direction_prevailing = %s, wind_speed_high_direction = %s '
			'WHERE summary_id = %s;'
		)
		cursor.execute(query, list(summary_values) + [wind_direction_prevailing, wind_speed_high_direction, summary_id])

		return summary_id, average_temperature

	def _aggregate_degree_days_and_wind_averages(self, cursor, summary_id, where_clause, where_arguments):
		query = (
			'SELECT sum(integrated_heating_degree_days), sum(integrated_cooling_degree_days) '
			'FROM weather_calculated_summary WHERE ' + where_clause + ';'
		)
		cursor.execute(query, where_arguments)
		hdd, cdd = cursor.fetchone()

		query = (
			'SELECT wind_speed_high_10_minute_average, wind_speed_high_10_minute_average_direction, '
			'wind_speed_high_10_minute_average_start, wind_speed_high_10_minute_average_end '
			'FROM weather_calculated_summary WHERE ' + where_clause +
			' AND wind_speed_high_10_minute_average IS NOT NULL '
			'ORDER BY wind_speed_high_10_minute_average DESC LIMIT 1;'
		)
		cursor.execute(query, where_arguments)
		wind_values = cursor.fetchone()
		wsh10ma = wsh10mad = wsh10mas = wsh10mae = None
		if wind_values:
			wsh10ma, wsh10mad, wsh10mas, wsh10mae = wind_values

		cursor.execute(
			'UPDATE weather_calculated_summary SET '
			'integrated_heating_degree_days = %s, integrated_cooling_degree_days = %s, '
			'wind_speed_high_10_minute_average = %s, wind_speed_high_10_minute_average_direction = %s, '
			'wind_speed_high_10_minute_average_start = %s, wind_speed_high_10_minute_average_end = %s '
			'WHERE summary_id = %s;',
			[hdd, cdd, wsh10ma, wsh10mad, wsh10mas, wsh10mae, summary_id]
		)

	def _aggregate_average_wind_run_distance(self, cursor, summary_id, column, where_clause, where_arguments):
		cursor.execute(
			'SELECT avg(wind_run_distance_total) FROM weather_calculated_summary WHERE ' + where_clause + ';',
			where_arguments,
		)
		wind_run_distance_total_average = cursor.fetchone()[0]

		if wind_run_distance_total_average:
			cursor.execute(
				'UPDATE weather_calculated_summary SET wind_run_distance_' + column + '_average = %s '
				'WHERE summary_id = %s;',
				[wind_run_distance_total_average, summary_id],
			)

	def find_new_rain_events(self):
		found_rain_events = 0
		ongoing_rain_events = 0
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

				# This is the start of a new rain event.
				last_rain = start_record[0]
				event_total_rain = start_record[1]
				event_rain_rates = [start_record[2]]
				event_max_rain_rate = event_rain_rates[0]
				event_max_rate_time = last_rain
				# At a 1-minute resolution (the max), 400 records is greater than 3 hours, so we can limit to that
				# This limit might have to be increased if the 3-hour rain event threshold is changed
				cursor.execute(
					'SELECT timestamp_station, rain_total, rain_rate_high FROM weather_archive_record '
					'WHERE timestamp_station > %s ORDER BY timestamp_station LIMIT 400;',
					[start_record[0]],
				)
				for (timestamp_station, rain_total, rain_rate_high) in cursor:
					if (timestamp_station - last_rain).total_seconds() > THREE_HOURS_IN_SECONDS:
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

				try:
					cursor.fetchall()  # Fetch remaining rows to prevent an error.
				except mysql.connector.errors.InterfaceError:
					# This just means there were no remaining rows
					pass

				if (datetime.datetime.now(self.station_time_zone).replace(tzinfo=None) - last_rain).total_seconds() < THREE_HOURS_IN_SECONDS:
					# This is an ongoing rain event, so don't record the end yet.
					last_rain = None
					ongoing_rain_events = 1
				else:
					found_rain_events += 1

				average_rate = (sum(event_rain_rates) / len(event_rain_rates)).quantize(HUNDREDTHS)

				cursor.execute(
					'INSERT INTO weather_rain_event (timestamp_start, timestamp_end, timestamp_rain_rate_high, '
					'rain_total, rain_rate_average, rain_rate_high) VALUES (%s, %s, %s, %s, %s, %s) '
					'ON DUPLICATE KEY UPDATE timestamp_end = %s, timestamp_rain_rate_high = %s, rain_total = %s, '
					'rain_rate_average = %s, rain_rate_high = %s;',
					[
						start_record[0], last_rain, event_max_rate_time, event_total_rain, average_rate,
						event_max_rain_rate, last_rain, event_max_rate_time, event_total_rain, average_rate,
						event_max_rain_rate,
					],
				)
				self._connection.commit()

				if not last_rain:
					break

		return found_rain_events, ongoing_rain_events

	def get_newest_timestamp(self):
		with self._get_cursor('SELECT max(timestamp_weatherlink) FROM weather_archive_record;', []) as cursor:
			return cursor.fetchone()[0]
