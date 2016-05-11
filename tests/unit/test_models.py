from __future__ import absolute_import

import curses.ascii
from datetime import (
	datetime,
	timedelta,
)
from decimal import Decimal
import os
import struct
from unittest import TestCase

from weatherlink.models import (
	convert_datetime_to_timestamp,
	convert_timestamp_to_datetime,
	BarometricTrend,
	LoopRecord,
	RainCollectorTypeSerial,
	RainCollectorTypeDatabase,
	WindDirection,
)


class TestTimestampConversion(TestCase):
	def test_convert_datetime_to_timestamp(self):
		self.assertEqual(
			416351713,
			convert_datetime_to_timestamp(datetime(2012, 6, 17, 15, 5, 0)),
		)
		self.assertEqual(
			544474613,
			convert_datetime_to_timestamp(datetime(2016, 3, 20, 15, 25, 0)),
		)
		self.assertEqual(
			546898420,
			convert_datetime_to_timestamp(datetime(2016, 4, 25, 5, 0, 0)),
		)
		self.assertEqual(
			546898520,
			convert_datetime_to_timestamp(datetime(2016, 4, 25, 6, 0, 0)),
		)
		self.assertEqual(
			546964056,
			convert_datetime_to_timestamp(datetime(2016, 4, 26, 6, 0, 0)),
		)
		self.assertEqual(
			547946906,
			convert_datetime_to_timestamp(datetime(2016, 5, 9, 4, 10, 0)),
		)

	def test_convert_timestamp_to_datetime(self):
		self.assertEqual(
			datetime(2012, 6, 17, 15, 5, 0),
			convert_timestamp_to_datetime(416351713),
		)
		self.assertEqual(
			datetime(2016, 3, 20, 15, 25, 0),
			convert_timestamp_to_datetime(544474613),
		)
		self.assertEqual(
			datetime(2016, 4, 25, 5, 0, 0),
			convert_timestamp_to_datetime(546898420),
		)
		self.assertEqual(
			datetime(2016, 4, 25, 6, 0, 0),
			convert_timestamp_to_datetime(546898520),
		)
		self.assertEqual(
			datetime(2016, 4, 26, 6, 0, 0),
			convert_timestamp_to_datetime(546964056),
		)
		self.assertEqual(
			datetime(2016, 5, 9, 4, 10, 0),
			convert_timestamp_to_datetime(547946906),
		)

	def test_two_way_convert(self):
		start = datetime(2012, 6, 17, 15, 5, 0)
		for i in range(0, 100000):
			now = start + timedelta(minutes=i)
			self.assertEqual(now, convert_timestamp_to_datetime(convert_datetime_to_timestamp(now)))

		start = datetime(2015, 11, 11, 11, 11, 0)
		for i in range(0, 100000):
			now = start + timedelta(minutes=i)
			self.assertEqual(now, convert_timestamp_to_datetime(convert_datetime_to_timestamp(now)))

		start = datetime(2021, 12, 11, 10, 9, 0)
		for i in range(0, 100000):
			now = start + timedelta(minutes=i)
			self.assertEqual(now, convert_timestamp_to_datetime(convert_datetime_to_timestamp(now)))

	def test_predictable_order(self):
		self.assertGreater(
			convert_datetime_to_timestamp(datetime(2016, 5, 9, 12, 1, 0)),
			convert_datetime_to_timestamp(datetime(2016, 5, 9, 12, 0, 0)),
		)
		self.assertGreater(
			convert_datetime_to_timestamp(datetime(2031, 12, 31, 11, 59, 0)),
			convert_datetime_to_timestamp(datetime(1996, 1, 1, 0, 0, 0)),
		)


class TestBarometricTrend(TestCase):
	def test_expected_values(self):
		self.assertEqual(BarometricTrend.falling_rapidly, BarometricTrend(-60))
		self.assertEqual(BarometricTrend.falling_slowly, BarometricTrend(-20))
		self.assertEqual(BarometricTrend.steady, BarometricTrend(0))
		self.assertEqual(BarometricTrend.rising_slowly, BarometricTrend(20))
		self.assertEqual(BarometricTrend.rising_rapidly, BarometricTrend(60))

	def test_unexpected_values(self):
		for i in range(-100, -60) + range(-59, -20) + range(-19, 0) + range(1, 20) + range(21, 60) + range(61, 101):
			with self.assertRaises(ValueError):
				BarometricTrend(i)


class TestWindDirection(TestCase):
	def test_expected_values(self):
		self.assertEqual(WindDirection.N, WindDirection(0))
		self.assertEqual(WindDirection.NNE, WindDirection(1))
		self.assertEqual(WindDirection.NE, WindDirection(2))
		self.assertEqual(WindDirection.ENE, WindDirection(3))
		self.assertEqual(WindDirection.E, WindDirection(4))
		self.assertEqual(WindDirection.ESE, WindDirection(5))
		self.assertEqual(WindDirection.SE, WindDirection(6))
		self.assertEqual(WindDirection.SSE, WindDirection(7))
		self.assertEqual(WindDirection.S, WindDirection(8))
		self.assertEqual(WindDirection.SSW, WindDirection(9))
		self.assertEqual(WindDirection.SW, WindDirection(10))
		self.assertEqual(WindDirection.WSW, WindDirection(11))
		self.assertEqual(WindDirection.W, WindDirection(12))
		self.assertEqual(WindDirection.WNW, WindDirection(13))
		self.assertEqual(WindDirection.NW, WindDirection(14))
		self.assertEqual(WindDirection.NNW, WindDirection(15))

	def test_unexpected_values(self):
		for i in range(-100, 0) + range(16, 100):
			with self.assertRaises(ValueError):
				WindDirection(i)

	def test_expected_degrees(self):
		for i in range(350, 360) + range(1, 12):
			self.assertEqual(WindDirection.N, WindDirection.from_degrees(i), i)

		for i in range(12, 35):
			self.assertEqual(WindDirection.NNE, WindDirection.from_degrees(i), i)

		for i in range(35, 57):
			self.assertEqual(WindDirection.NE, WindDirection.from_degrees(i), i)

		for i in range(57, 80):
			self.assertEqual(WindDirection.ENE, WindDirection.from_degrees(i), i)

		for i in range(80, 101):
			self.assertEqual(WindDirection.E, WindDirection.from_degrees(i), i)

		for i in range(102, 125):
			self.assertEqual(WindDirection.ESE, WindDirection.from_degrees(i), i)

		for i in range(125, 147):
			self.assertEqual(WindDirection.SE, WindDirection.from_degrees(i), i)

		for i in range(147, 170):
			self.assertEqual(WindDirection.SSE, WindDirection.from_degrees(i), i)

		for i in range(170, 192):
			self.assertEqual(WindDirection.S, WindDirection.from_degrees(i), i)

		for i in range(192, 215):
			self.assertEqual(WindDirection.SSW, WindDirection.from_degrees(i), i)

		for i in range(215, 237):
			self.assertEqual(WindDirection.SW, WindDirection.from_degrees(i), i)

		for i in range(273, 260):
			self.assertEqual(WindDirection.WSW, WindDirection.from_degrees(i), i)

		for i in range(260, 282):
			self.assertEqual(WindDirection.W, WindDirection.from_degrees(i), i)

		for i in range(282, 305):
			self.assertEqual(WindDirection.WNW, WindDirection.from_degrees(i), i)

		for i in range(305, 327):
			self.assertEqual(WindDirection.NW, WindDirection.from_degrees(i), i)

		for i in range(327, 350):
			self.assertEqual(WindDirection.NNW, WindDirection.from_degrees(i), i)

	def test_unexpected_degrees(self):
		for i in range(-100, 0) + range(361, 500):
			self.assertIsNone(WindDirection.from_degrees(i), i)


class TestRainCollectorTypeSerial(TestCase):
	def test_inches_0_01(self):
		self.assertEqual(RainCollectorTypeSerial.inches_0_01, RainCollectorTypeSerial(0x00))

		self.assertEqual(Decimal('0.01'), RainCollectorTypeSerial.inches_0_01.clicks_to_inches(1))
		self.assertEqual(Decimal('0.70'), RainCollectorTypeSerial.inches_0_01.clicks_to_inches(70))

		self.assertAlmostEqual(
			Decimal('0.0254'),
			RainCollectorTypeSerial.inches_0_01.clicks_to_centimeters(1),
			delta=0.000001,
		)
		self.assertAlmostEqual(
			Decimal('1.778'),
			RainCollectorTypeSerial.inches_0_01.clicks_to_centimeters(70),
			delta=0.000001,
		)

	def test_millimeters_0_1(self):
		self.assertEqual(RainCollectorTypeSerial.millimeters_0_1, RainCollectorTypeSerial(0x20))

		self.assertAlmostEqual(
			Decimal('0.00393701'),
			RainCollectorTypeSerial.millimeters_0_1.clicks_to_inches(1),
			delta=0.000001,
		)
		self.assertAlmostEqual(
			Decimal('0.275591'),
			RainCollectorTypeSerial.millimeters_0_1.clicks_to_inches(70),
			delta=0.000001,
		)

		self.assertEqual(Decimal('0.01'), RainCollectorTypeSerial.millimeters_0_1.clicks_to_centimeters(1))
		self.assertEqual(Decimal('0.70'), RainCollectorTypeSerial.millimeters_0_1.clicks_to_centimeters(70))

	def test_millimeters_0_2(self):
		self.assertEqual(RainCollectorTypeSerial.millimeters_0_2, RainCollectorTypeSerial(0x10))

		self.assertAlmostEqual(
			Decimal('0.00787402'),
			RainCollectorTypeSerial.millimeters_0_2.clicks_to_inches(1),
			delta=0.000001,
		)
		self.assertAlmostEqual(
			Decimal('0.551181'),
			RainCollectorTypeSerial.millimeters_0_2.clicks_to_inches(70),
			delta=0.000001,
		)

		self.assertEqual(Decimal('0.02'), RainCollectorTypeSerial.millimeters_0_2.clicks_to_centimeters(1))
		self.assertEqual(Decimal('1.40'), RainCollectorTypeSerial.millimeters_0_2.clicks_to_centimeters(70))


class TestRainCollectorTypeDatabase(TestCase):
	def inches_0_1(self):
		self.assertEqual(RainCollectorTypeDatabase.inches_0_1, RainCollectorTypeDatabase(0x1000))

		self.assertEqual(Decimal('0.1'), RainCollectorTypeDatabase.inches_0_1.clicks_to_inches(1))
		self.assertEqual(Decimal('7.0'), RainCollectorTypeDatabase.inches_0_1.clicks_to_inches(70))

		self.assertAlmostEqual(
			Decimal('0.254'),
			RainCollectorTypeDatabase.inches_0_1.clicks_to_centimeters(1),
			delta=0.000001,
		)
		self.assertAlmostEqual(
			Decimal('17.78'),
			RainCollectorTypeDatabase.inches_0_1.clicks_to_centimeters(70),
			delta=0.000001,
		)

	def test_inches_0_01(self):
		self.assertEqual(RainCollectorTypeDatabase.inches_0_01, RainCollectorTypeDatabase(0x1000))

		self.assertEqual(Decimal('0.01'), RainCollectorTypeDatabase.inches_0_01.clicks_to_inches(1))
		self.assertEqual(Decimal('0.70'), RainCollectorTypeDatabase.inches_0_01.clicks_to_inches(70))

		self.assertAlmostEqual(
			Decimal('0.0254'),
			RainCollectorTypeDatabase.inches_0_01.clicks_to_centimeters(1),
			delta=0.000001,
		)
		self.assertAlmostEqual(
			Decimal('1.778'),
			RainCollectorTypeDatabase.inches_0_01.clicks_to_centimeters(70),
			delta=0.000001,
		)

	def test_millimeters_0_1(self):
		self.assertEqual(RainCollectorTypeDatabase.millimeters_0_1, RainCollectorTypeDatabase(0x6000))

		self.assertAlmostEqual(
			Decimal('0.00393701'),
			RainCollectorTypeDatabase.millimeters_0_1.clicks_to_inches(1),
			delta=0.000001,
		)
		self.assertAlmostEqual(
			Decimal('0.275591'),
			RainCollectorTypeDatabase.millimeters_0_1.clicks_to_inches(70),
			delta=0.000001,
		)

		self.assertEqual(Decimal('0.01'), RainCollectorTypeDatabase.millimeters_0_1.clicks_to_centimeters(1))
		self.assertEqual(Decimal('0.70'), RainCollectorTypeDatabase.millimeters_0_1.clicks_to_centimeters(70))

	def test_millimeters_0_2(self):
		self.assertEqual(RainCollectorTypeDatabase.millimeters_0_2, RainCollectorTypeDatabase(0x2000))

		self.assertAlmostEqual(
			Decimal('0.00787402'),
			RainCollectorTypeDatabase.millimeters_0_2.clicks_to_inches(1),
			delta=0.000001,
		)
		self.assertAlmostEqual(
			Decimal('0.551181'),
			RainCollectorTypeDatabase.millimeters_0_2.clicks_to_inches(70),
			delta=0.000001,
		)

		self.assertEqual(Decimal('0.02'), RainCollectorTypeDatabase.millimeters_0_2.clicks_to_centimeters(1))
		self.assertEqual(Decimal('1.40'), RainCollectorTypeDatabase.millimeters_0_2.clicks_to_centimeters(70))

	def test_millimeters_1_0(self):
		self.assertEqual(RainCollectorTypeDatabase.millimeters_1_0, RainCollectorTypeDatabase(0x3000))

		self.assertAlmostEqual(
			Decimal('0.0393701'),
			RainCollectorTypeDatabase.millimeters_1_0.clicks_to_inches(1),
			delta=0.00001,
		)
		self.assertAlmostEqual(
			Decimal('2.75591'),
			RainCollectorTypeDatabase.millimeters_1_0.clicks_to_inches(70),
			delta=0.00001,
		)

		self.assertEqual(Decimal('0.1'), RainCollectorTypeDatabase.millimeters_1_0.clicks_to_centimeters(1))
		self.assertEqual(Decimal('7.0'), RainCollectorTypeDatabase.millimeters_1_0.clicks_to_centimeters(70))


class TestLoopRecord(TestCase):
	def test_load_loop_1_from_connection_not_implemented(self):
		with self.assertRaises(NotImplementedError):
			LoopRecord.load_loop_1_from_connection(None)

	def test_load_loop_2_from_connection(self):
		with open(
			os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'data/sample-loop2-data.bin'),
			'rb',
		) as handle:
			# This is some data that was written to the file when the sample loop packets were first captured
			# from the socket using the test-loop-packet.py script.
			timestamp_read, sep, ack = struct.unpack_from('<L1sB', handle.read(6))

			self.assertIsNotNone(timestamp_read)
			self.assertEqual('\n', sep)
			self.assertEqual(curses.ascii.ACK, ack)

			records = [LoopRecord.load_loop_2_from_connection(handle) for _ in range(0, 15)]
			self.assertEqual(15, len(records))

			record = records[0]
			self.assertIsNotNone(record)
			self.assertTrue(record.crc_match)
			self.assertEqual(2, record.record_type)
			self.assertEqual(BarometricTrend.rising_slowly, record.barometric_trend)
			self.assertEqual(Decimal('29.961'), record.barometric_pressure)
			self.assertEqual(Decimal('68.3'), record.temperature_inside)
			self.assertEqual(63, record.humidity_inside)
			self.assertEqual(Decimal('61.3'), record.temperature_outside)
			self.assertEqual(Decimal('91'), record.humidity_outside)
			self.assertEqual(Decimal('59'), record.dew_point)
			self.assertEqual(Decimal('2'), record.wind_speed)
			self.assertEqual(Decimal('0.8'), record.wind_speed_10_minute_average)
			self.assertEqual(Decimal('0.5'), record.wind_speed_2_minute_average)
			self.assertEqual(Decimal('0.4'), record.wind_speed_10_minute_gust)
			self.assertEqual(313, record.wind_direction_degrees)
			self.assertEqual(WindDirection.NW, record.wind_direction)
			self.assertEqual(336, record.wind_speed_10_minute_gust_direction_degrees)
			self.assertEqual(WindDirection.NNW, record.wind_speed_10_minute_gust_direction)
			self.assertEqual(0, record.rain_rate_clicks)
			self.assertIsNone(record.rain_rate)
			self.assertEqual(5, record.rain_clicks_this_storm)
			self.assertEqual(Decimal('0.05'), record.rain_amount_this_storm)
			self.assertEqual(5, record.rain_clicks_today)
			self.assertEqual(Decimal('0.05'), record.rain_amount_today)
			self.assertEqual(0, record.rain_clicks_15_minutes)
			self.assertIsNone(record.rain_amount_15_minutes)
			self.assertEqual(0, record.rain_clicks_1_hour)
			self.assertIsNone(record.rain_amount_1_hour)
			self.assertEqual(5, record.rain_clicks_24_hours)
			self.assertEqual(Decimal('0.05'), record.rain_amount_24_hours)
			self.assertIsNone(record.thsw_index)
			self.assertIsNone(record.uv_index)
			self.assertIsNone(record.solar_radiation)
			self.assertIsNone(record.evapotranspiration)
			self.assertEqual(15, record.minute_in_hour)

			record = records[2]
			self.assertIsNotNone(record)
			self.assertTrue(record.crc_match)
			self.assertEqual(2, record.record_type)
			self.assertEqual(BarometricTrend.rising_slowly, record.barometric_trend)
			self.assertEqual(Decimal('29.961'), record.barometric_pressure)
			self.assertEqual(Decimal('68.3'), record.temperature_inside)
			self.assertEqual(63, record.humidity_inside)
			self.assertEqual(Decimal('61.3'), record.temperature_outside)
			self.assertEqual(Decimal('91'), record.humidity_outside)
			self.assertEqual(Decimal('59'), record.dew_point)
			self.assertEqual(Decimal('2'), record.wind_speed)
			self.assertEqual(Decimal('0.8'), record.wind_speed_10_minute_average)
			self.assertEqual(Decimal('0.6'), record.wind_speed_2_minute_average)
			self.assertEqual(Decimal('0.4'), record.wind_speed_10_minute_gust)
			self.assertEqual(359, record.wind_direction_degrees)
			self.assertEqual(WindDirection.N, record.wind_direction)
			self.assertEqual(336, record.wind_speed_10_minute_gust_direction_degrees)
			self.assertEqual(WindDirection.NNW, record.wind_speed_10_minute_gust_direction)
			self.assertEqual(0, record.rain_rate_clicks)
			self.assertIsNone(record.rain_rate)
			self.assertEqual(5, record.rain_clicks_this_storm)
			self.assertEqual(Decimal('0.05'), record.rain_amount_this_storm)
			self.assertEqual(5, record.rain_clicks_today)
			self.assertEqual(Decimal('0.05'), record.rain_amount_today)
			self.assertEqual(0, record.rain_clicks_15_minutes)
			self.assertIsNone(record.rain_amount_15_minutes)
			self.assertEqual(0, record.rain_clicks_1_hour)
			self.assertIsNone(record.rain_amount_1_hour)
			self.assertEqual(5, record.rain_clicks_24_hours)
			self.assertEqual(Decimal('0.05'), record.rain_amount_24_hours)
			self.assertIsNone(record.thsw_index)
			self.assertIsNone(record.uv_index)
			self.assertIsNone(record.solar_radiation)
			self.assertIsNone(record.evapotranspiration)
			self.assertEqual(15, record.minute_in_hour)

			record = records[4]
			self.assertIsNotNone(record)
			self.assertTrue(record.crc_match)
			self.assertEqual(2, record.record_type)
			self.assertEqual(BarometricTrend.rising_slowly, record.barometric_trend)
			self.assertEqual(Decimal('29.961'), record.barometric_pressure)
			self.assertEqual(Decimal('68.3'), record.temperature_inside)
			self.assertEqual(63, record.humidity_inside)
			self.assertEqual(Decimal('61.3'), record.temperature_outside)
			self.assertEqual(Decimal('91'), record.humidity_outside)
			self.assertEqual(Decimal('59'), record.dew_point)
			self.assertEqual(Decimal('1'), record.wind_speed)
			self.assertEqual(Decimal('0.8'), record.wind_speed_10_minute_average)
			self.assertEqual(Decimal('0.6'), record.wind_speed_2_minute_average)
			self.assertEqual(Decimal('0.4'), record.wind_speed_10_minute_gust)
			self.assertEqual(313, record.wind_direction_degrees)
			self.assertEqual(WindDirection.NW, record.wind_direction)
			self.assertEqual(336, record.wind_speed_10_minute_gust_direction_degrees)
			self.assertEqual(WindDirection.NNW, record.wind_speed_10_minute_gust_direction)
			self.assertEqual(0, record.rain_rate_clicks)
			self.assertIsNone(record.rain_rate)
			self.assertEqual(5, record.rain_clicks_this_storm)
			self.assertEqual(Decimal('0.05'), record.rain_amount_this_storm)
			self.assertEqual(5, record.rain_clicks_today)
			self.assertEqual(Decimal('0.05'), record.rain_amount_today)
			self.assertEqual(0, record.rain_clicks_15_minutes)
			self.assertIsNone(record.rain_amount_15_minutes)
			self.assertEqual(0, record.rain_clicks_1_hour)
			self.assertIsNone(record.rain_amount_1_hour)
			self.assertEqual(5, record.rain_clicks_24_hours)
			self.assertEqual(Decimal('0.05'), record.rain_amount_24_hours)
			self.assertIsNone(record.thsw_index)
			self.assertIsNone(record.uv_index)
			self.assertIsNone(record.solar_radiation)
			self.assertIsNone(record.evapotranspiration)
			self.assertEqual(15, record.minute_in_hour)

			record = records[14]
			self.assertIsNotNone(record)
			self.assertTrue(record.crc_match)
			self.assertEqual(2, record.record_type)
			self.assertEqual(BarometricTrend.rising_slowly, record.barometric_trend)
			self.assertEqual(Decimal('29.961'), record.barometric_pressure)
			self.assertEqual(Decimal('68.3'), record.temperature_inside)
			self.assertEqual(63, record.humidity_inside)
			self.assertEqual(Decimal('61.3'), record.temperature_outside)
			self.assertEqual(Decimal('91'), record.humidity_outside)
			self.assertEqual(Decimal('59'), record.dew_point)
			self.assertEqual(Decimal('1'), record.wind_speed)
			self.assertEqual(Decimal('0.8'), record.wind_speed_10_minute_average)
			self.assertEqual(Decimal('0.7'), record.wind_speed_2_minute_average)
			self.assertEqual(Decimal('0.4'), record.wind_speed_10_minute_gust)
			self.assertEqual(313, record.wind_direction_degrees)
			self.assertEqual(WindDirection.NW, record.wind_direction)
			self.assertEqual(336, record.wind_speed_10_minute_gust_direction_degrees)
			self.assertEqual(WindDirection.NNW, record.wind_speed_10_minute_gust_direction)
			self.assertEqual(0, record.rain_rate_clicks)
			self.assertIsNone(record.rain_rate)
			self.assertEqual(5, record.rain_clicks_this_storm)
			self.assertEqual(Decimal('0.05'), record.rain_amount_this_storm)
			self.assertEqual(5, record.rain_clicks_today)
			self.assertEqual(Decimal('0.05'), record.rain_amount_today)
			self.assertEqual(0, record.rain_clicks_15_minutes)
			self.assertIsNone(record.rain_amount_15_minutes)
			self.assertEqual(0, record.rain_clicks_1_hour)
			self.assertIsNone(record.rain_amount_1_hour)
			self.assertEqual(5, record.rain_clicks_24_hours)
			self.assertEqual(Decimal('0.05'), record.rain_amount_24_hours)
			self.assertIsNone(record.thsw_index)
			self.assertIsNone(record.uv_index)
			self.assertIsNone(record.solar_radiation)
			self.assertIsNone(record.evapotranspiration)
			self.assertEqual(15, record.minute_in_hour)
