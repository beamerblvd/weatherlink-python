from __future__ import absolute_import

import datetime
import decimal
import struct

"""
The data formats in this file were obtained from Davis WeatherLink documentation in the following locations:
	- http://www.davisnet.com/support/weather/download/VantageSerialProtocolDocs_v261.pdf
	- C:/WeatherLink/Readme 6.0.rtf
"""

DASH_LARGE = 32767
DASH_LARGE_NEGATIVE = -32768
DASH_ZERO = 0
DASH_SMALL = 255

RAIN_COLLECTOR_TYPE_0_1_IN = 0x0000
RAIN_COLLECTOR_TYPE_0_01_IN = 0x1000
RAIN_COLLECTOR_TYPE_0_2_MM = 0x2000
RAIN_COLLECTOR_TYPE_1_0_MM = 0x3000
RAIN_COLLECTOR_TYPE_0_1_MM = 0x6000

RAIN_COLLECTOR_TYPE_AMOUNT_TO_INCHES = {
	RAIN_COLLECTOR_TYPE_0_1_IN: decimal.Decimal('0.1'),
	RAIN_COLLECTOR_TYPE_0_01_IN: decimal.Decimal('0.01'),
	RAIN_COLLECTOR_TYPE_0_2_MM: decimal.Decimal('0.00787402'),
	RAIN_COLLECTOR_TYPE_1_0_MM: decimal.Decimal('0.0393701'),
	RAIN_COLLECTOR_TYPE_0_1_MM: decimal.Decimal('0.00393701'),
}

RAIN_COLLECTOR_TYPE_AMOUNT_TO_CENTIMETERS = {
	RAIN_COLLECTOR_TYPE_0_1_IN: decimal.Decimal('0.254'),
	RAIN_COLLECTOR_TYPE_0_01_IN: decimal.Decimal('0.0254'),
	RAIN_COLLECTOR_TYPE_0_2_MM: decimal.Decimal('0.02'),
	RAIN_COLLECTOR_TYPE_1_0_MM: decimal.Decimal('0.1'),
	RAIN_COLLECTOR_TYPE_0_1_MM: decimal.Decimal('0.01'),
}

WIND_DIRECTION_CODE_MAP = [
	'N',  # 0
	'NNE',  # 1
	'NE',  # 2
	'ENE',  # 3
	'E',  # 4
	'ESE',  # 5
	'SE',  # 6
	'SSE',  # 7
	'S',  # 8
	'SSW',  # 9
	'SW',  # 10
	'WSW',  # 11
	'W',  # 12
	'WNW',  # 13
	'NW',  # 14
	'NNW',  # 15
]

BAROMETER_TREND_MAP = {
	-60: 'Falling Rapidly',
	-20: 'Falling Slowly',
	0: 'Steady',
	20: 'Rising Slowly',
	60: 'Rising Rapidly',
}

STRAIGHT_NUMBER = int

STRAIGHT_DECIMAL = decimal.Decimal

_TENTHS = decimal.Decimal('0.1')
TENTHS = lambda x: x * _TENTHS

_HUNDREDTHS = decimal.Decimal('0.01')
HUNDREDTHS = lambda x: x * _HUNDREDTHS

_THOUSANDTHS = decimal.Decimal('0.001')
THOUSANDTHS = lambda x: x * _THOUSANDTHS


def convert_datetime_to_timestamp(d):
	if isinstance(d, datetime.datetime):
		return ((d.day + (d.month * 32) + ((d.year - 2000) * 512)) << 16) + (d.minute + (d.hour * 100))
	return d


def convert_timestamp_to_datetime(timestamp):
	date_part = timestamp >> 16
	time_part = timestamp - (date_part << 16)

	year = (date_part / 512) + 2000
	month = (date_part - ((year - 2000) * 512)) / 32
	day = date_part - ((year - 2000) * 512) - (month * 32)
	hour = time_part / 100
	minute = time_part - (hour * 100)

	return datetime.datetime(year, month, day, hour, minute)


class RecordDict(dict):
	def __getattr__(self, name):
		return self.__getitem__(name)

	def __setattr__(self, name, value):
		self[name] = value


class Header(RecordDict):
	VERSION_CODE_AND_COUNT_FORMAT = '=16sl'
	VERSION_CODE_AND_COUNT_LENGTH = 20

	def __init__(self, version_code, record_count, day_indexes):
		super(Header, self).__init__()
		self.version_code = version_code
		self.record_count = record_count
		self.day_indexes = day_indexes

	@classmethod
	def load_from_wlk(cls, file_handle):
		version_and_count = struct.unpack_from(
			cls.VERSION_CODE_AND_COUNT_FORMAT,
			file_handle.read(cls.VERSION_CODE_AND_COUNT_LENGTH),
		)
		day_indexes = []

		for i in range(0, 32):
			day_indexes.append(DayIndex.load_from_wlk(file_handle))

		return cls(version_and_count[0], version_and_count[1], day_indexes)


class DayIndex(RecordDict):
	DAY_INDEX_FORMAT = '=hl'
	DAY_INDEX_LENGTH = 6

	def __init__(self, record_count, start_index):
		super(DayIndex, self).__init__()
		self.record_count = record_count
		self.start_index = start_index

	@classmethod
	def load_from_wlk(cls, file_handle):
		return cls(*struct.unpack_from(
			cls.DAY_INDEX_FORMAT,
			file_handle.read(cls.DAY_INDEX_LENGTH),
		))


class DailySummary(RecordDict):
	DAILY_SUMMARY_FORMAT = (
		'=bx'  # '2' plus a reserved byte [ignored]
		'h'  # number of minutes accounted for in this day's records
		'2h'  # hi and low outside temps in tenths of degres
		'2h'  # hi and low inside temps in tenths of degrees
		'h'  # average outside temp in tenths of degrees
		'h'  # average inside temp in tenths of degrees
		'2h'  # hi and low wind chill temps in tenths of degrees
		'2h'  # hi and low dew point temps in tenths of degrees
		'h'  # average wind chill temp in tenths of degrees
		'h'  # average dew point temp in tenths of degrees
		'2h'  # hi and low outside humitidy in tenths of percents
		'2h'  # hi and low inside humitidy in tenths of percents
		'h'  # average outside humitidy in tenths of percents
		'2h'  # hi and low barometric pressure in thousandths of inches of mercury
		'h'  # average barometric pressure in thousandths of inches of mercury
		'h'  # high wind speed in tenths of miles per hour
		'h'  # average wind speed in tenths of miles per hour
		'h'  # daily wind run total in tenths of miles
		'h'  # highest 10-minute average wind speed in tenths of miles per hour
		'b'  # direction code (0-15, 255) for high wind speed
		'b'  # direction code for highest 10-minute average wind speed
		'h'  # daily rain total in thousandths of inches
		'h'  # hi daily rain rate in hundredths of inches per hour
		'2x'  # daily UV dose (ignored)
		'x'  # high UV dose (ignored)
		'27x'  # time values (ignored)
		'bx'  # '3' plus a reserved byte [ignored]
		'2x'  # today's weather (unsupported and ignored)
		'h'  # total number of wind packets
		'8x'  # solar, sunlight, and evapotranspiration (ignored)
		'2h'  # hi and low heat index in tenths of degrees
		'h'  # average heat index in tenths of degrees
		'4x'  # hi and low temperature-humidity-sun-wind (THSW) index in tenths of degrees (ignored)
		'2h'  # hi and low temperature-humidity-wind (THW) index in tenths of degrees
		'h'  # integrated heating degree days in tenths of degrees
		'2h'  # hi and low wet bulb temp in tenths of degrees
		'h'  # average wet bulb temp in tenths of degrees
		'24x'  # unused space for direction bins (ignored)
		'15x'  # unused space for time values (ignored)
		'h'  # integrated cooling degree days in tenths of degrees
		'11x'  # reserved bytes (ignored)
	)
	DAILY_SUMMARY_LENGTH = 88 * 2
	DAILY_SUMMARY_VERIFICATION_MAP = {
		0: 2,
		30: 3,
	}
	DAILY_SUMMARY_ATTRIBUTE_MAP = (
		('ds1_version', STRAIGHT_NUMBER, None, ),
		('minutes', STRAIGHT_NUMBER, None, ),
		('temperature_outside_high', TENTHS, DASH_LARGE_NEGATIVE, ),
		('temperature_outside_low', TENTHS, DASH_LARGE, ),
		('temperature_inside_high', TENTHS, DASH_LARGE_NEGATIVE, ),
		('temperature_inside_low', TENTHS, DASH_LARGE, ),
		('temperature_outside_average', TENTHS, DASH_LARGE, ),
		('temperature_inside_average', TENTHS, DASH_LARGE, ),
		('wind_chill_high', TENTHS, DASH_LARGE_NEGATIVE, ),
		('wind_chill_low', TENTHS, DASH_LARGE, ),
		('dew_point_high', TENTHS, DASH_LARGE_NEGATIVE, ),
		('dew_point_low', TENTHS, DASH_LARGE, ),
		('wind_chill_average', TENTHS, DASH_LARGE, ),
		('dew_point_average', TENTHS, DASH_LARGE, ),
		('humidity_outside_high', TENTHS, DASH_SMALL, ),
		('humidity_outside_low', TENTHS, DASH_SMALL, ),
		('humidity_inside_high', TENTHS, DASH_SMALL, ),
		('humidity_inside_low', TENTHS, DASH_SMALL, ),
		('humidity_outside_average', TENTHS, DASH_SMALL, ),
		('barometric_pressure_high', THOUSANDTHS, DASH_ZERO, ),
		('barometric_pressure_low', THOUSANDTHS, DASH_ZERO, ),
		('barometric_pressure_average', THOUSANDTHS, DASH_ZERO, ),
		('wind_speed_high', TENTHS, DASH_ZERO, ),
		('wind_speed_average', TENTHS, DASH_ZERO, ),
		('wind_daily_run', TENTHS, DASH_ZERO, ),
		('wind_speed_high_10_minute_average', TENTHS, DASH_LARGE_NEGATIVE, ),
		('wind_speed_high_direction', WIND_DIRECTION_CODE_MAP.__getitem__, DASH_SMALL, ),
		('wind_speed_high_10_minute_average_direction', WIND_DIRECTION_CODE_MAP.__getitem__, DASH_SMALL, ),
		('rain_total', THOUSANDTHS, None, ),
		('rain_rate_high', HUNDREDTHS, None, ),
		('ds2_version', STRAIGHT_NUMBER, None, ),
		('total_wind_packets', STRAIGHT_NUMBER, DASH_LARGE_NEGATIVE, ),
		('heat_index_high', TENTHS, DASH_LARGE_NEGATIVE, ),
		('heat_index_low', TENTHS, DASH_LARGE, ),
		('heat_index_average', TENTHS, DASH_LARGE, ),
		('thw_index_high', TENTHS, DASH_LARGE_NEGATIVE, ),
		('thw_index_low', TENTHS, DASH_LARGE, ),
		('integrated_heating_degree_days', TENTHS, DASH_ZERO, ),
		('temperature_wet_bulb_high', TENTHS, DASH_LARGE_NEGATIVE, ),
		('temperature_wet_bulb_low', TENTHS, DASH_LARGE, ),
		('temperature_wet_bulb_average', TENTHS, DASH_LARGE, ),
		('integrated_cooling_degree_days', TENTHS, DASH_ZERO, ),
	)

	@classmethod
	def load_from_wlk(cls, file_handle, year, month, day):
		arguments = struct.unpack_from(
			cls.DAILY_SUMMARY_FORMAT,
			file_handle.read(cls.DAILY_SUMMARY_LENGTH),
		)

		for k, v in cls.DAILY_SUMMARY_VERIFICATION_MAP.iteritems():
			assert arguments[k] == v

		kwargs = {}
		for i, v in enumerate(arguments):
			if i not in cls.DAILY_SUMMARY_VERIFICATION_MAP:
				k = cls.DAILY_SUMMARY_ATTRIBUTE_MAP[i][0]
				if v == cls.DAILY_SUMMARY_ATTRIBUTE_MAP[i][2]:
					kwargs[k] = None
				else:
					kwargs[k] = cls.DAILY_SUMMARY_ATTRIBUTE_MAP[i][1](v)

		return cls(date=datetime.date(year, month, day), **kwargs)


class ArchiveIntervalRecord(RecordDict):
	RECORD_FORMAT_WLK = (
		'=b'  # '1'
		'b'  # minutes in this record
		'2x'  # icon flags and oter flags (ignored)
		'h'  # minutes past midnight
		'h'  # current outside temp in tenths of degrees
		'h'  # hi outside temp this time period in tenths of degrees
		'h'  # low outside temp this time period in tenths of degrees
		'h'  # current inside temp in tenths of degrees
		'h'  # barometric pressure in thousandths of inches of mercury
		'h'  # outside humitidy in tenths of percents
		'h'  # inside humitidy in tenths of percents
		'H'  # raw rain clicks (clicks masked with type)
		'h'  # high rain rate this time period in raw clicks/hr
		'h'  # wind speed in tenths of miles per hour
		'h'  # hi wind speed this time period in tenths of miles per hour
		'b'  # previaling wind direction (0-15, 255)
		'b'  # hi wind speed direction (0-15, 255)
		'h'  # number of wind samples this time period
		'h'  # average solar rad this time period in watts / meter squared
		'h'  # high solar radiation this time period in watts / meter squared
		'B'  # UV index
		'B'  # high UV index during this time period
		'50x'  # other unused items (ignored)
	)
	RECORD_FORMAT_DOWNLOAD = (
		'=hh'  # date and time stamps
		'h'  # current outside temp in tenths of degrees
		'h'  # hi outside temp this time period in tenths of degrees
		'h'  # low outside temp this time period in tenths of degrees
		'H'  # raw rain clicks (clicks masked with type)
		'H'  # high rain rate this time period in raw clicks/hr
		'H'  # barometric pressure in thousandths of inches of mercury
		'h'  # average solar rad this time period in watts / meter squared
		'H'  # number of wind samples this time period
		'h'  # current inside temp in tenths of degrees
		'B'  # inside humitidy in tenths of percents
		'B'  # outside humitidy in tenths of percents
		'B'  # wind speed in tenths of miles per hour
		'B'  # hi wind speed this time period in tenths of miles per hour
		'B'  # hi wind speed direction (0-15, 255)
		'B'  # prevailing wind direction (0-15, 255)
		'B'  # UV index
		'B'  # evapotranspiration in thousandths of inches (only during hour on top of hour)
		'h'  # high solar radiation this time period in watts / meter squared
		'B'  # high UV index during this time period
		'9x'  # unused for now (ignored)
		'B'  # Download record type (0xFF = Rev A, 0x00 = Rev B)
		'9x'  # unused for now (ignored)
	)
	RECORD_LENGTH_WLK = 88
	RECORD_LENGTH_DOWNLOAD = 52
	RECORD_VERIFICATION_MAP_WLK = {
		0: 1,
	}
	RECORD_VERIFICATION_MAP_DOWNLOAD = {
		21: 0,
	}
	RECORD_SPECIAL_HANDLING_WLK = {10, 11}
	RECORD_SPECIAL_HANDLING_DOWNLOAD = {0, 1, 5, 6}
	RECORD_ATTRIBUTE_MAP_WLK = (
		('record_version', STRAIGHT_NUMBER, None, ),
		('minutes_covered', STRAIGHT_NUMBER, None, ),
		('minutes_past_midnight', STRAIGHT_NUMBER, None, ),
		('temperature_outside', TENTHS, DASH_LARGE, ),
		('temperature_outside_high', TENTHS, DASH_LARGE_NEGATIVE, ),
		('temperature_outside_low', TENTHS, DASH_LARGE, ),
		('temperature_inside', TENTHS, DASH_LARGE, ),
		('barometric_pressure', THOUSANDTHS, DASH_ZERO, ),
		('humidity_outside', TENTHS, DASH_SMALL, ),
		('humidity_inside', TENTHS, DASH_SMALL, ),
		('__special', STRAIGHT_NUMBER, None, ),
		('__special', STRAIGHT_NUMBER, None, ),
		('wind_speed', TENTHS, DASH_SMALL, ),
		('wind_speed_high', TENTHS, DASH_ZERO, ),
		('wind_direction_prevailing', WIND_DIRECTION_CODE_MAP.__getitem__, DASH_SMALL, ),
		('wind_direction_speed_high', WIND_DIRECTION_CODE_MAP.__getitem__, DASH_SMALL, ),
		('number_of_wind_samples', STRAIGHT_NUMBER, DASH_ZERO, ),
		('solar_radiation', STRAIGHT_NUMBER, DASH_LARGE_NEGATIVE, ),
		('solar_radiation_high', STRAIGHT_NUMBER, DASH_LARGE_NEGATIVE, ),
		('uv_index', TENTHS, DASH_SMALL, ),
		('uv_index_high', TENTHS, DASH_SMALL, ),
	)
	RECORD_ATTRIBUTE_MAP_DOWNLOAD = (
		('__special', STRAIGHT_NUMBER, None, ),
		('__special', STRAIGHT_NUMBER, None, ),
		('temperature_outside', TENTHS, DASH_LARGE, ),
		('temperature_outside_high', TENTHS, DASH_LARGE_NEGATIVE, ),
		('temperature_outside_low', TENTHS, DASH_LARGE, ),
		('__special', STRAIGHT_NUMBER, None, ),
		('__special', STRAIGHT_NUMBER, None, ),
		('barometric_pressure', THOUSANDTHS, DASH_ZERO, ),
		('solar_radiation', STRAIGHT_NUMBER, DASH_LARGE, ),
		('number_of_wind_samples', STRAIGHT_NUMBER, DASH_ZERO, ),
		('temperature_inside', TENTHS, DASH_LARGE, ),
		('humidity_inside', STRAIGHT_NUMBER, DASH_SMALL, ),
		('humidity_outside', STRAIGHT_NUMBER, DASH_SMALL, ),
		('wind_speed', STRAIGHT_DECIMAL, DASH_SMALL, ),
		('wind_speed_high', STRAIGHT_DECIMAL, DASH_ZERO, ),
		('wind_direction_speed_high', WIND_DIRECTION_CODE_MAP.__getitem__, DASH_SMALL, ),
		('wind_direction_prevailing', WIND_DIRECTION_CODE_MAP.__getitem__, DASH_SMALL, ),
		('uv_index', TENTHS, DASH_SMALL, ),
		('evapotranspiration', THOUSANDTHS, DASH_ZERO, ),
		('solar_radiation_high', STRAIGHT_NUMBER, DASH_LARGE, ),
		('uv_index_high', TENTHS, DASH_SMALL, ),
		('record_version', STRAIGHT_NUMBER, None, ),
	)

	@classmethod
	def load_from_wlk(cls, file_handle, year, month, day):
		arguments = struct.unpack_from(
			cls.RECORD_FORMAT_WLK,
			file_handle.read(cls.RECORD_LENGTH_WLK),
		)

		for k, v in cls.RECORD_VERIFICATION_MAP_WLK.iteritems():
			assert arguments[k] == v

		kwargs = {}
		for i, v in enumerate(arguments):
			if i not in cls.RECORD_VERIFICATION_MAP_WLK and i not in cls.RECORD_SPECIAL_HANDLING_WLK:
				k = cls.RECORD_ATTRIBUTE_MAP_WLK[i][0]
				if v == cls.RECORD_ATTRIBUTE_MAP_WLK[i][2]:
					kwargs[k] = None
				else:
					kwargs[k] = cls.RECORD_ATTRIBUTE_MAP_WLK[i][1](v)

		record = cls(**kwargs)

		rain_code = arguments[10]
		rain_collector_type = rain_code & 0xF000
		rain_clicks = rain_code & 0x0FFF
		rain_rate_clicks = arguments[11]

		record.rain_collector_type = rain_collector_type
		record.rain_amount_clicks = rain_clicks
		record.rain_rate_clicks = rain_rate_clicks
		record.rain_amount = RAIN_COLLECTOR_TYPE_AMOUNT_TO_INCHES[rain_collector_type] * rain_clicks
		record.rain_rate = RAIN_COLLECTOR_TYPE_AMOUNT_TO_INCHES[rain_collector_type] * rain_rate_clicks

		record.date = datetime.datetime(year, month, day, 0, 0) + datetime.timedelta(minutes=record.minutes_past_midnight)
		record.timestamp = convert_datetime_to_timestamp(record.date)

		return record

	@classmethod
	def load_from_download(cls, response_handle, minutes_covered):
		arguments = struct.unpack_from(
			cls.RECORD_FORMAT_DOWNLOAD,
			response_handle.read(cls.RECORD_LENGTH_DOWNLOAD),
		)
		if arguments[0] < 1:
			return None

		for k, v in cls.RECORD_VERIFICATION_MAP_DOWNLOAD.iteritems():
			assert arguments[k] == v

		kwargs = {}
		for i, v in enumerate(arguments):
			if i not in cls.RECORD_VERIFICATION_MAP_DOWNLOAD and i not in cls.RECORD_SPECIAL_HANDLING_DOWNLOAD:
				k = cls.RECORD_ATTRIBUTE_MAP_DOWNLOAD[i][0]
				if v == cls.RECORD_ATTRIBUTE_MAP_DOWNLOAD[i][2]:
					kwargs[k] = None
				else:
					kwargs[k] = cls.RECORD_ATTRIBUTE_MAP_DOWNLOAD[i][1](v)

		record = cls(**kwargs)

		record.minutes_covered = minutes_covered

		# The online download does not contain this information, unfortunately
		rain_collector_type = RAIN_COLLECTOR_TYPE_0_01_IN

		rain_clicks = arguments[5]
		rain_rate_clicks = arguments[6]

		record.rain_collector_type = rain_collector_type
		record.rain_amount_clicks = rain_clicks
		record.rain_rate_clicks = rain_rate_clicks
		record.rain_amount = RAIN_COLLECTOR_TYPE_AMOUNT_TO_INCHES[rain_collector_type] * rain_clicks
		record.rain_rate = RAIN_COLLECTOR_TYPE_AMOUNT_TO_INCHES[rain_collector_type] * rain_rate_clicks

		record.timestamp = (arguments[0] << 16) + arguments[1]
		record.date = convert_timestamp_to_datetime(record.timestamp)

		return record


class LoopRecord(RecordDict):
	RECORD_LENGTH = 99

	LOOP1_RECORD_TYPE = 0
	LOOP2_RECORD_TYPE = 1

	LOOP2_RECORD_FORMAT = (
		'<3s'  # String 'LOO'
		'b'  # barometer trend
		'B'  # Should be 1 for "LOOP 2" (0 would indicate "LOOP 1")
		'H'  # Unused, should be 0x7FFF
		'H'  # Barometer in thousandths of inches of mercury
		'h'  # Inside temperature in tenths of degrees Fahrenheit
		'B'  # Inside humidity in whole percents
		'h'  # Outside temperature in tenths of degrees Fahrenheit
		'B'  # Wind speed in MPH
		'B'  # Unused, should be 0xFF
		'H'  # Wind direction in degrees, 0 = no wind, 1 = nearly N, 90 = E, 180 = S, 270 = W, 360 = N
		'H'  # 10-minute wind average speed in tenths of MPH
		'H'  # 2-minute wind average speed in tenths of MPH
		'H'  # 10-minute wind gust speed in tenths of MPH
		'H'  # 10-minute wind gust direction in degrees
		'H'  # Unused, should be 0x7FFF
		'H'  # Unused, should be 0x7FFF
		'h'  # Dew point in whole degrees Fahrenheit
		'B'  # Unused, should be 0xFF
		'B'  # Outside humidity in whole percents
		'B'  # Unused, should be 0xFF
		'h'  # Heat index in whole degrees Fahrenheit
		'h'  # Wind chill in whole degrees Fahrenheit
		'h'  # THSW index in whole degrees Fahrenheit
		'H'  # Rain rate in clicks/hour
		'B'  # UV Index
		'H'  # Solar radiation in watts per square meter
		'H'  # Number of rain clicks this storm
		'2x'  # Useless start date of this storm, which we don't care about
		'H'  # Number of rain clicks today
		'H'  # Number of rain clicks last 15 minutes
		'H'  # Number of rain clicks last 1 hour
		'H'  # Daily total evapotranspiration in thousandths of inches
		'H'  # Number of rain clicks last 24 hours
		'11x'  # Barometer calibration-related settings and readings
		'B'  # Unused, should be 0xFF
		'x'  # Unused field filled with undefined data
		'6x'  # Information about what's displayed on the console graph, which we don't care about
		'B'  # The minute within the hour, 0-59
		'3x'  # Information about what's displayed on the console graph, which we don't care about
		'H'  # Unused, should be 0x7FFF
		'H'  # Unused, should be 0x7FFF
		'H'  # Unused, should be 0x7FFF
		'H'  # Unused, should be 0x7FFF
		'H'  # Unused, should be 0x7FFF
		'H'  # Unused, should be 0x7FFF
		'c'  # Should be '\n'
		'c'  # Should be '\r'
		'H'  # Cyclic redundancy check (CRC)
	)

	LOOP2_RECORD_VERIFICATION_MAP_WLK = {
		0: 'LOO',
		2: 1,
		3: 0x7FFF,
		9: 0xFF,
		15: 0x7FFF,
		16: 0x7FFF,
		18: 0xFF,
		20: 0xFF,
		33: 0xFF,
		35: 0x7FFF,
		36: 0x7FFF,
		37: 0x7FFF,
		38: 0x7FFF,
		39: 0x7FFF,
		40: 0x7FFF,
		41: '\n',
		42: '\r',
	}

	LOOP2_RECORD_SPECIAL_HANDLING = frozenset(LOOP2_RECORD_VERIFICATION_MAP_WLK.keys())

	LOOP2_RECORD_ATTRIBUTE_MAP = (
		('_special', STRAIGHT_NUMBER, None, ),
		('barometer_trend', STRAIGHT_NUMBER, 80, ),
		('_special', STRAIGHT_NUMBER, None, ),
		('_special', STRAIGHT_NUMBER, None, ),
		('barometric_pressure', THOUSANDTHS, DASH_ZERO, ),
		('temperature_inside', TENTHS, DASH_LARGE, ),
		('humidity_inside', STRAIGHT_NUMBER, DASH_SMALL, ),
		('temperature_outside', TENTHS, DASH_LARGE, ),
		('wind_speed', STRAIGHT_DECIMAL, DASH_SMALL, ),
		('_special', STRAIGHT_NUMBER, None, ),
		('wind_direction_degrees', STRAIGHT_NUMBER, DASH_ZERO, ),
		('wind_speed_10_minute_average', TENTHS, DASH_ZERO, ),
		('wind_speed_2_minute_average', TENTHS, DASH_ZERO, ),
		('wind_speed_10_minute_gust', TENTHS, DASH_ZERO, ),
		('wind_speed_10_minute_gust_direction_degrees', STRAIGHT_NUMBER, DASH_ZERO, ),
		('_special', STRAIGHT_NUMBER, None, ),
		('_special', STRAIGHT_NUMBER, None, ),
		('dew_point', STRAIGHT_DECIMAL, None, ),
		('_special', STRAIGHT_NUMBER, None, ),
		('humidity_outside', STRAIGHT_NUMBER, DASH_SMALL, ),
		('_special', STRAIGHT_NUMBER, None, ),
		('heat_index', STRAIGHT_NUMBER, None, ),
		('wind_chill', STRAIGHT_NUMBER, None, ),
		('thsw_index', STRAIGHT_NUMBER, None, ),
		('rain_rate_clicks', STRAIGHT_NUMBER, None, ),
		('uv_index', TENTHS, DASH_SMALL, ),
		('solar_radiation', STRAIGHT_NUMBER, DASH_LARGE, ),
		('rain_clicks_this_storm', STRAIGHT_NUMBER, None, ),
		('rain_clicks_today', STRAIGHT_NUMBER, None, ),
		('rain_clicks_15_minutes', STRAIGHT_NUMBER, None, ),
		('rain_clicks_1_hour', STRAIGHT_NUMBER, None, ),
		('evapotranspiration', THOUSANDTHS, DASH_ZERO, ),
		('rain_clicks_24_hours', STRAIGHT_NUMBER, None, ),
		('_special', STRAIGHT_NUMBER, None),
		('minute_in_hour', STRAIGHT_NUMBER, 60, ),
	)

	@classmethod
	def load_loop_1_2_from_connection(cls, socket_file):
		arguments = cls._get_loop_1_arguments(socket_file, True)
		arguments.update(cls._get_loop_2_arguments(socket_file))
		return cls(**arguments)

	@classmethod
	def load_loop_1_from_connection(cls, socket_file):
		return cls(**cls._get_loop_1_arguments(socket_file))

	@classmethod
	def load_loop_2_from_connection(cls, socket_file):
		return cls(**cls._get_loop_2_arguments(socket_file))

	@classmethod
	def _get_loop_1_arguments(cls, socket_file, unique_only=False):
		arguments = {}

		# TODO: LOOP 1

		return arguments

	@classmethod
	def _get_loop_2_arguments(cls, socket_file):
		data = socket_file.read(cls.RECORD_LENGTH)
		if calculate_weatherlink_crc(data) != 0:
			print 'CRC mismatch'

		unpacked = struct.unpack_from(cls.LOOP2_RECORD_FORMAT, data)

		for k, v in cls.LOOP2_RECORD_VERIFICATION_MAP_WLK.iteritems():
			assert unpacked[k] == v

		arguments = {}

		last = len(cls.LOOP2_RECORD_ATTRIBUTE_MAP)
		for i, v in enumerate(unpacked):
			if (i < last and i not in cls.LOOP2_RECORD_VERIFICATION_MAP_WLK and
						i not in cls.LOOP2_RECORD_SPECIAL_HANDLING):
				k = cls.LOOP2_RECORD_ATTRIBUTE_MAP[i][0]
				if v == cls.LOOP2_RECORD_ATTRIBUTE_MAP[i][2]:
					arguments[k] = None
				else:
					arguments[k] = cls.LOOP2_RECORD_ATTRIBUTE_MAP[i][1](v)

		return arguments


WEATHERLINK_CRC_TABLE = (
	0x0, 0x1021, 0x2042, 0x3063, 0x4084, 0x50a5, 0x60c6, 0x70e7,
	0x8108, 0x9129, 0xa14a, 0xb16b, 0xc18c, 0xd1ad, 0xe1ce, 0xf1ef,
	0x1231, 0x210, 0x3273, 0x2252, 0x52b5, 0x4294, 0x72f7, 0x62d6,
	0x9339, 0x8318, 0xb37b, 0xa35a, 0xd3bd, 0xc39c, 0xf3ff, 0xe3de,
	0x2462, 0x3443, 0x420, 0x1401, 0x64e6, 0x74c7, 0x44a4, 0x5485,
	0xa56a, 0xb54b, 0x8528, 0x9509, 0xe5ee, 0xf5cf, 0xc5ac, 0xd58d,
	0x3653, 0x2672, 0x1611, 0x630, 0x76d7, 0x66f6, 0x5695, 0x46b4,
	0xb75b, 0xa77a, 0x9719, 0x8738, 0xf7df, 0xe7fe, 0xd79d, 0xc7bc,
	0x48c4, 0x58e5, 0x6886, 0x78a7, 0x840, 0x1861, 0x2802, 0x3823,
	0xc9cc, 0xd9ed, 0xe98e, 0xf9af, 0x8948, 0x9969, 0xa90a, 0xb92b,
	0x5af5, 0x4ad4, 0x7ab7, 0x6a96, 0x1a71, 0xa50, 0x3a33, 0x2a12,
	0xdbfd, 0xcbdc, 0xfbbf, 0xeb9e, 0x9b79, 0x8b58, 0xbb3b, 0xab1a,
	0x6ca6, 0x7c87, 0x4ce4, 0x5cc5, 0x2c22, 0x3c03, 0xc60, 0x1c41,
	0xedae, 0xfd8f, 0xcdec, 0xddcd, 0xad2a, 0xbd0b, 0x8d68, 0x9d49,
	0x7e97, 0x6eb6, 0x5ed5, 0x4ef4, 0x3e13, 0x2e32, 0x1e51, 0xe70,
	0xff9f, 0xefbe, 0xdfdd, 0xcffc, 0xbf1b, 0xaf3a, 0x9f59, 0x8f78,
	0x9188, 0x81a9, 0xb1ca, 0xa1eb, 0xd10c, 0xc12d, 0xf14e, 0xe16f,
	0x1080, 0xa1, 0x30c2, 0x20e3, 0x5004, 0x4025, 0x7046, 0x6067,
	0x83b9, 0x9398, 0xa3fb, 0xb3da, 0xc33d, 0xd31c, 0xe37f, 0xf35e,
	0x2b1, 0x1290, 0x22f3, 0x32d2, 0x4235, 0x5214, 0x6277, 0x7256,
	0xb5ea, 0xa5cb, 0x95a8, 0x8589, 0xf56e, 0xe54f, 0xd52c, 0xc50d,
	0x34e2, 0x24c3, 0x14a0, 0x481, 0x7466, 0x6447, 0x5424, 0x4405,
	0xa7db, 0xb7fa, 0x8799, 0x97b8, 0xe75f, 0xf77e, 0xc71d, 0xd73c,
	0x26d3, 0x36f2, 0x691, 0x16b0, 0x6657, 0x7676, 0x4615, 0x5634,
	0xd94c, 0xc96d, 0xf90e, 0xe92f, 0x99c8, 0x89e9, 0xb98a, 0xa9ab,
	0x5844, 0x4865, 0x7806, 0x6827, 0x18c0, 0x8e1, 0x3882, 0x28a3,
	0xcb7d, 0xdb5c, 0xeb3f, 0xfb1e, 0x8bf9, 0x9bd8, 0xabbb, 0xbb9a,
	0x4a75, 0x5a54, 0x6a37, 0x7a16, 0xaf1, 0x1ad0, 0x2ab3, 0x3a92,
	0xfd2e, 0xed0f, 0xdd6c, 0xcd4d, 0xbdaa, 0xad8b, 0x9de8, 0x8dc9,
	0x7c26, 0x6c07, 0x5c64, 0x4c45, 0x3ca2, 0x2c83, 0x1ce0, 0xcc1,
	0xef1f, 0xff3e, 0xcf5d, 0xdf7c, 0xaf9b, 0xbfba, 0x8fd9, 0x9ff8,
	0x6e17, 0x7e36, 0x4e55, 0x5e74, 0x2e93, 0x3eb2, 0xed1, 0x1ef0,
)


def calculate_weatherlink_crc(data_bytes):
	crc = 0
	cast_with_ord = isinstance(data_bytes, basestring)
	for i, byte in enumerate(data_bytes):
		if cast_with_ord:
			byte = ord(byte)
		crc = WEATHERLINK_CRC_TABLE[((crc >> 8) & 0xFF) ^ byte] ^ ((crc << 8) & 0xFF00)
	return crc
