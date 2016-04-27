from __future__ import absolute_import

import datetime
import decimal
import struct

"""
The data formats in this file were obtained from Davis WeatherLink documentation in the following locations:
  - http://www.davisnet.com/support/weather/download/VantageSerialProtocolDocs_v261.pdf
  - C:/WeatherLink/Readmy 6.0.rtf
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
		try:
			super(RecordDict, self).__getattr__(name)
		except AttributeError:
			return self.__getitem__(name)

	def __setattr__(self, name, value):
		self[name] = value


class Header(RecordDict):
	VERSION_CODE_AND_COUNT_FORMAT = '=16sl'
	VERSION_CODE_AND_COUNT_LENGTH = 20

	def __init__(self, version_code, record_count, day_indexes):
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
		'24x'   # unused space for direction bins (ignored)
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
		('integrated_heating_degree_days', TENTHS, DASH_ZERO ),
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


class InstantaneousRecord(RecordDict):
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
	def load_from_download(cls, response_handle):
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
