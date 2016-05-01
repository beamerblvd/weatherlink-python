from datetime import datetime
from decimal import Decimal
import imp
import os
from unittest import (
	skip,
	TestCase
)

from weatherlink import utils


class TestUnitConversion(TestCase):
	def test_convert_fahrenheit_to_kelvin(self):
		self.assertEqual(Decimal('255.372'), utils.convert_fahrenheit_to_kelvin(0))
		self.assertEqual(Decimal('263.706'), utils.convert_fahrenheit_to_kelvin(15))
		self.assertEqual(Decimal('273.15'), utils.convert_fahrenheit_to_kelvin(32))
		self.assertEqual(Decimal('278.15'), utils.convert_fahrenheit_to_kelvin(41))
		self.assertEqual(Decimal('291.483'), utils.convert_fahrenheit_to_kelvin(65))
		self.assertEqual(Decimal('295.372'), utils.convert_fahrenheit_to_kelvin(72))
		self.assertEqual(Decimal('310.928'), utils.convert_fahrenheit_to_kelvin(100))
		self.assertEqual(Decimal('373.15'), utils.convert_fahrenheit_to_kelvin(212))

	def test_convert_kelvin_to_fahrenheit(self):
		self.assertAlmostEqual(Decimal('0'), utils.convert_kelvin_to_fahrenheit(Decimal('255.372')), delta=0.01)
		self.assertAlmostEqual(Decimal('15'), utils.convert_kelvin_to_fahrenheit(Decimal('263.706')), delta=0.01)
		self.assertAlmostEqual(Decimal('32'), utils.convert_kelvin_to_fahrenheit(Decimal('273.15')), delta=0.01)
		self.assertAlmostEqual(Decimal('41'), utils.convert_kelvin_to_fahrenheit(Decimal('278.15')), delta=0.01)
		self.assertAlmostEqual(Decimal('65'), utils.convert_kelvin_to_fahrenheit(Decimal('291.483')), delta=0.01)
		self.assertAlmostEqual(Decimal('72'), utils.convert_kelvin_to_fahrenheit(Decimal('295.372')), delta=0.01)
		self.assertAlmostEqual(Decimal('100'), utils.convert_kelvin_to_fahrenheit(Decimal('310.928')), delta=0.01)
		self.assertAlmostEqual(Decimal('212'), utils.convert_kelvin_to_fahrenheit(Decimal('373.15')), delta=0.01)

	def test_convert_fahrenheit_to_celsius(self):
		self.assertAlmostEqual(Decimal('-17.7778'), utils.convert_fahrenheit_to_celsius(0), delta=0.01)
		self.assertAlmostEqual(Decimal('-9.44444'), utils.convert_fahrenheit_to_celsius(15), delta=0.01)
		self.assertAlmostEqual(Decimal('0'), utils.convert_fahrenheit_to_celsius(32), delta=0.01)
		self.assertAlmostEqual(Decimal('5'), utils.convert_fahrenheit_to_celsius(41), delta=0.01)
		self.assertAlmostEqual(Decimal('18.3333'), utils.convert_fahrenheit_to_celsius(65), delta=0.01)
		self.assertAlmostEqual(Decimal('22.2222'), utils.convert_fahrenheit_to_celsius(72), delta=0.01)
		self.assertAlmostEqual(Decimal('37.7778'), utils.convert_fahrenheit_to_celsius(100), delta=0.01)
		self.assertAlmostEqual(Decimal('100'), utils.convert_fahrenheit_to_celsius(212), delta=0.01)

	def test_convert_celsius_to_fahrenheit(self):
		self.assertAlmostEqual(Decimal('0'), utils.convert_celsius_to_fahrenheit(Decimal('-17.7778')), delta=0.01)
		self.assertAlmostEqual(Decimal('15'), utils.convert_celsius_to_fahrenheit(Decimal('-9.44444')), delta=0.01)
		self.assertAlmostEqual(Decimal('32'), utils.convert_celsius_to_fahrenheit(Decimal('0')), delta=0.01)
		self.assertAlmostEqual(Decimal('41'), utils.convert_celsius_to_fahrenheit(Decimal('5')), delta=0.01)
		self.assertAlmostEqual(Decimal('65'), utils.convert_celsius_to_fahrenheit(Decimal('18.3333')), delta=0.01)
		self.assertAlmostEqual(Decimal('72'), utils.convert_celsius_to_fahrenheit(Decimal('22.2222')), delta=0.01)
		self.assertAlmostEqual(Decimal('100'), utils.convert_celsius_to_fahrenheit(Decimal('37.7778')), delta=0.01)
		self.assertAlmostEqual(Decimal('212'), utils.convert_celsius_to_fahrenheit(Decimal('100')), delta=0.01)

	def test_round_trip_kelvin_fahrenheit(self):
		self.assertEqual(Decimal('0'), utils.convert_kelvin_to_fahrenheit(utils.convert_fahrenheit_to_kelvin(0)))
		self.assertAlmostEqual(
			Decimal('15'),
			utils.convert_kelvin_to_fahrenheit(utils.convert_fahrenheit_to_kelvin(15)),
			delta=0.01,
		)
		self.assertEqual(Decimal('32'), utils.convert_kelvin_to_fahrenheit(utils.convert_fahrenheit_to_kelvin(32)))
		self.assertEqual(Decimal('41'), utils.convert_kelvin_to_fahrenheit(utils.convert_fahrenheit_to_kelvin(41)))
		self.assertAlmostEqual(
			Decimal('65'),
			utils.convert_kelvin_to_fahrenheit(utils.convert_fahrenheit_to_kelvin(65)),
			delta=0.01,
		)
		self.assertEqual(Decimal('72'), utils.convert_kelvin_to_fahrenheit(utils.convert_fahrenheit_to_kelvin(72)))
		self.assertEqual(Decimal('100'), utils.convert_kelvin_to_fahrenheit(utils.convert_fahrenheit_to_kelvin(100)))
		self.assertEqual(Decimal('212'), utils.convert_kelvin_to_fahrenheit(utils.convert_fahrenheit_to_kelvin(212)))

	def test_round_trip_celsius_fahrenheit(self):
		self.assertEqual(Decimal('0'), utils.convert_celsius_to_fahrenheit(utils.convert_fahrenheit_to_celsius(0)))
		self.assertAlmostEqual(
			Decimal('15'),
			utils.convert_celsius_to_fahrenheit(utils.convert_fahrenheit_to_celsius(15)),
			delta=0.01,
		)
		self.assertEqual(Decimal('32'), utils.convert_celsius_to_fahrenheit(utils.convert_fahrenheit_to_celsius(32)))
		self.assertEqual(Decimal('41'), utils.convert_celsius_to_fahrenheit(utils.convert_fahrenheit_to_celsius(41)))
		self.assertAlmostEqual(
			Decimal('65'),
			utils.convert_celsius_to_fahrenheit(utils.convert_fahrenheit_to_celsius(65)),
			delta=0.01,
		)
		self.assertEqual(Decimal('72'), utils.convert_celsius_to_fahrenheit(utils.convert_fahrenheit_to_celsius(72)))
		self.assertEqual(Decimal('100'), utils.convert_celsius_to_fahrenheit(utils.convert_fahrenheit_to_celsius(100)))
		self.assertEqual(Decimal('212'), utils.convert_celsius_to_fahrenheit(utils.convert_fahrenheit_to_celsius(212)))

	def test_convert_inches_of_mercury_to_kilopascals(self):
		self.assertAlmostEqual(
			Decimal('3.38639'),
			utils.convert_inches_of_mercury_to_kilopascals(Decimal('1')),
			delta=0.01,
		)
		self.assertAlmostEqual(
			Decimal('33.8639'),
			utils.convert_inches_of_mercury_to_kilopascals(Decimal('10')),
			delta=0.01,
		)
		self.assertAlmostEqual(
			Decimal('101.11757'),
			utils.convert_inches_of_mercury_to_kilopascals(Decimal('29.86')),
			delta=0.01,
		)
		self.assertAlmostEqual(
			Decimal('101.5578'),
			utils.convert_inches_of_mercury_to_kilopascals(Decimal('29.99')),
			delta=0.01,
		)
		self.assertAlmostEqual(
			Decimal('101.96416'),
			utils.convert_inches_of_mercury_to_kilopascals(Decimal('30.11')),
			delta=0.01,
		)

	def test_convert_inches_of_mercury_to_millibars(self):
		self.assertAlmostEqual(
			Decimal('33.8639'),
			utils.convert_inches_of_mercury_to_millibars(Decimal('1')),
			delta=0.01,
		)
		self.assertAlmostEqual(
			Decimal('338.639'),
			utils.convert_inches_of_mercury_to_millibars(Decimal('10')),
			delta=0.01,
		)
		self.assertAlmostEqual(
			Decimal('1011.1757'),
			utils.convert_inches_of_mercury_to_millibars(Decimal('29.86')),
			delta=0.01,
		)
		self.assertAlmostEqual(
			Decimal('1015.578'),
			utils.convert_inches_of_mercury_to_millibars(Decimal('29.99')),
			delta=0.01,
		)
		self.assertAlmostEqual(
			Decimal('1019.6416'),
			utils.convert_inches_of_mercury_to_millibars(Decimal('30.11')),
			delta=0.01,
		)

	def test_convert_miles_per_hour_to_meters_per_second(self):
		self.assertAlmostEqual(
			Decimal('0.44704'),
			utils.convert_miles_per_hour_to_meters_per_second(Decimal('1')),
			delta=0.0001,
		)
		self.assertAlmostEqual(
			Decimal('6.7056'),
			utils.convert_miles_per_hour_to_meters_per_second(Decimal('15')),
			delta=0.0001,
		)
		self.assertAlmostEqual(
			Decimal('16.5405'),
			utils.convert_miles_per_hour_to_meters_per_second(Decimal('37')),
			delta=0.0001,
		)
		self.assertAlmostEqual(
			Decimal('86.7258'),
			utils.convert_miles_per_hour_to_meters_per_second(Decimal('194')),
			delta=0.001,
		)
		self.assertAlmostEqual(
			Decimal('1313.404'),
			utils.convert_miles_per_hour_to_meters_per_second(Decimal('2938')),
			delta=0.01,
		)


class TestIndexCalculation(TestCase):
	# This heat index chart comes from NOAA/NWS: http://www.nws.noaa.gov/os/heat/heat_index.shtml
	HEAT_INDEX_X_AXIS_TEMP = (80, 82, 84, 86, 88, 90, 92, 94, 96, 98, 100, 102, 104, 106, 108, 110, )
	HEAT_INDEX_Y_AXIS_HUMIDITY = (40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100, )
	HEAT_INDEX_CHART = (
		(80, 81, 83, 85, 88, 91, 94, 97, 101, 105, 109, 114, 119, 124, 130, 136, ),  # 40%
		(80, 82, 84, 87, 89, 93, 96, 100, 104, 109, 114, 119, 124, 130, 137, ),  # 45%
		(81, 83, 85, 88, 91, 95, 99, 103, 108, 113, 118, 124, 131, 137, ),  # 50%
		(81, 84, 86, 89, 93, 97, 101, 106, 112, 117, 124, 130, 137, ),  # 55%
		(82, 84, 88, 91, 95, 100, 105, 110, 116, 123, 129, 137, ),  # 60%
		(82, 85, 89, 93, 98, 103, 108, 114, 121, 128, 136, ),  # 65%
		(83, 86, 90, 95, 100, 105, 112, 119, 126, 134, ),  # 70%
		(84, 88, 92, 97, 103, 109, 116, 124, 132, ),  # 75%
		(84, 89, 94, 100, 106, 113, 121, 129, ),  # 80%
		(85, 90, 96, 102, 110, 117, 126, 135, ),  # 85%
		(86, 91, 98, 105, 113, 122, 131, ),  # 90%
		(87, 93, 100, 108, 117, 127, ),  # 95%
		(88, 95, 103, 112, 121, 132, ),  # 100%
	)

	WIND_CHILL_X_AXIS_TEMP = (40, 35, 30, 25, 20, 15, 10, 5, 0, -5, -10, -15, -20, -25, -30, -35, -40, -45)
	WIND_CHILL_Y_AXIS_WIND = (5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60)
	WIND_CHILL_CHART = (
		(36, 31, 25, 19, 13, 7, 1, -5, -11, -16, -22, -28, -34, -40, -46, -52, -57, -63, ),  # 5mph
		(34, 27, 21, 15, 9, 3, -4, -10, -16, -22, -28, -35, -41, -47, -53, -59, -66, -72, ),  # 10mph
		(32, 25, 19, 13, 6, 0, -7, -13, -19, -26, -32, -39, -45, -51, -58, -64, -71, -77, ),  # 15mph
		(30, 24, 17, 11, 4, -2, -9, -15, -22, -29, -35, -42, -48, -55, -61, -68, -74, -81, ),  # 20mph
		(29, 23, 16, 9, 3, -4, -11, -17, -24, -31, -37, -44, -51, -58, -64, -71, -78, -84, ),  # 25mph
		(28, 22, 15, 8, 1, -5, -12, -19, -26, -33, -39, -46, -53, -60, -67, -73, -80, -87, ),  # 30mph
		(28, 21, 14, 7, 0, -7, -14, -21, -27, -34, -41, -48, -55, -62, -69, -76, -82, -89, ),  # 35mph
		(27, 20, 13, 6, -1, -8, -15, -22, -29, -36, -43, -50, -57, -64, -71, -78, -84, -91, ),  # 40mph
		(26, 19, 12, 5, -2, -9, -16, -23, -30, -37, -44, -51, -58, -65, -72, -79, -86, -93, ),  # 45mph
		(26, 19, 12, 4, -3, -10, -17, -24, -31, -38, -45, -52, -60, -67, -74, -81, -88, -95, ),  # 50mph
		(25, 18, 11, 4, -3, -11, -18, -25, -32, -39, -46, -54, -61, -68, -75, -82, -89, -97, ),  # 55mph
		(25, 17, 10, 3, -4, -11, -19, -26, -33, -40, -48, -55, -62, -69, -76, -84, -91, -98, ),  # 60mph
	)

	def test_calculate_heat_index_against_chart(self):
		assertions = 0

		for y, humidity in enumerate(self.HEAT_INDEX_Y_AXIS_HUMIDITY):
			for x, temperature in enumerate(self.HEAT_INDEX_X_AXIS_TEMP):
				if x < len(self.HEAT_INDEX_CHART[y]):
					assertions += 1
					try:
						self.assertAlmostEqual(
							self.HEAT_INDEX_CHART[y][x],
							utils.calculate_heat_index(Decimal(temperature), Decimal(humidity)),
							delta=1.3,
						)
					except AssertionError as e:
						ls = [a for a in e.args]
						ls.append('Temperature %s, humidity %s' % (temperature, humidity, ))
						e.args = ls
						raise e

		self.assertEqual(135, assertions)

	def test_calculate_heat_index_against_known_trouble_values(self):
		self.assertIsNone(utils.calculate_heat_index(Decimal('69.9'), Decimal('90')))
		self.assertAlmostEqual(Decimal('71'), utils.calculate_heat_index(Decimal('70'), Decimal('90')), delta=0.5)
		self.assertAlmostEqual(Decimal('68.5'), utils.calculate_heat_index(Decimal('70.0'), Decimal('5')), delta=0.1)
		self.assertAlmostEqual(Decimal('69.1'), utils.calculate_heat_index(Decimal('70.1'), Decimal('25')), delta=0.1)
		self.assertAlmostEqual(Decimal('69.5'), utils.calculate_heat_index(Decimal('70.1'), Decimal('42.5')), delta=0.1)
		self.assertAlmostEqual(Decimal('70.5'), utils.calculate_heat_index(Decimal('70.1'), Decimal('86')), delta=0.1)
		self.assertAlmostEqual(Decimal('68.7'), utils.calculate_heat_index(Decimal('70.2'), Decimal('5')), delta=0.1)
		self.assertAlmostEqual(Decimal('79.8'), utils.calculate_heat_index(Decimal('80'), Decimal('40')), delta=0.1)
		self.assertAlmostEqual(Decimal('85.3'), utils.calculate_heat_index(Decimal('80'), Decimal('86')), delta=0.1)
		self.assertAlmostEqual(Decimal('89.3'), utils.calculate_heat_index(Decimal('80'), Decimal('100')), delta=0.1)
		self.assertAlmostEqual(Decimal('83.5'), utils.calculate_heat_index(Decimal('81.5'), Decimal('58')), delta=0.1)
		self.assertAlmostEqual(Decimal('105.4'), utils.calculate_heat_index(Decimal('86'), Decimal('90')), delta=0.1)
		self.assertAlmostEqual(Decimal('90.1'), utils.calculate_heat_index(Decimal('95'), Decimal('12')), delta=0.1)
		self.assertAlmostEqual(Decimal('135.9'), utils.calculate_heat_index(Decimal('100'), Decimal('65')), delta=0.1)
		self.assertAlmostEqual(Decimal('107.0'), utils.calculate_heat_index(Decimal('111'), Decimal('12')), delta=0.1)

	def test_calculate_wind_chill_against_chart(self):
		assertions = 0

		for y, wind in enumerate(self.WIND_CHILL_Y_AXIS_WIND):
			for x, temperature in enumerate(self.WIND_CHILL_X_AXIS_TEMP):
				assertions += 1
				try:
					self.assertAlmostEqual(
						self.WIND_CHILL_CHART[y][x],
						utils.calculate_wind_chill(Decimal(temperature), Decimal(wind)),
						delta=0.5,
					)
				except AssertionError as e:
					ls = [a for a in e.args]
					ls.append('Temperature %s, wind %s' % (temperature, wind, ))
					e.args = ls
					raise e

		self.assertEqual(216, assertions)

	def test_calculate_wind_chill_against_known_trouble_values(self):
		self.assertIsNone(utils.calculate_wind_chill(Decimal('40.1'), Decimal('5')))
		self.assertAlmostEqual(Decimal('-10.5'), utils.calculate_wind_chill(Decimal('0'), Decimal('5')), delta=0.1)
		self.assertAlmostEqual(Decimal('-30.0'), utils.calculate_wind_chill(Decimal('0'), Decimal('45')), delta=0.1)
		self.assertAlmostEqual(Decimal('39.9'), utils.calculate_wind_chill(Decimal('39.9'), Decimal('0')), delta=0.1)
		self.assertAlmostEqual(Decimal('39.7'), utils.calculate_wind_chill(Decimal('39.9'), Decimal('2')), delta=0.1)
		self.assertAlmostEqual(Decimal('38.3'), utils.calculate_wind_chill(Decimal('39.9'), Decimal('3')), delta=0.1)
		self.assertAlmostEqual(Decimal('36.5'), utils.calculate_wind_chill(Decimal('40.0'), Decimal('5')), delta=0.1)
		self.assertAlmostEqual(Decimal('26.3'), utils.calculate_wind_chill(Decimal('40.0'), Decimal('45')), delta=0.1)

	def test_calculate_wet_bulb_temperature(self):
		self.assertAlmostEqual(
			Decimal('70.5'),
			utils.calculate_wet_bulb_temperature(Decimal('84.4'), Decimal('50'), Decimal('29.80')),
			delta=0.5,
		)
		self.assertAlmostEqual(
			Decimal('74.6'),
			utils.calculate_wet_bulb_temperature(Decimal('91.5'), Decimal('45'), Decimal('30.01')),
			delta=0.5,
		)
		self.assertAlmostEqual(
			Decimal('53.2'),
			utils.calculate_wet_bulb_temperature(Decimal('55.7'), Decimal('85'), Decimal('29.41')),
			delta=0.5,
		)

	def test_calculate_dew_point(self):
		self.assertAlmostEqual(Decimal('64.4'), utils.calculate_dew_point(Decimal('83.1'), Decimal('54')), delta=0.1)
		self.assertAlmostEqual(Decimal('64.0'), utils.calculate_dew_point(Decimal('82.1'), Decimal('55')), delta=0.1)
		self.assertAlmostEqual(Decimal('61.7'), utils.calculate_dew_point(Decimal('77.9'), Decimal('58')), delta=0.1)
		self.assertAlmostEqual(Decimal('53.6'), utils.calculate_dew_point(Decimal('54.5'), Decimal('97')), delta=0.1)
		self.assertAlmostEqual(Decimal('31.8'), utils.calculate_dew_point(Decimal('32.0'), Decimal('99')), delta=0.1)
		self.assertAlmostEqual(Decimal('59.2'), utils.calculate_dew_point(Decimal('95.0'), Decimal('31')), delta=0.1)
		self.assertAlmostEqual(Decimal('55.4'), utils.calculate_dew_point(Decimal('55.7'), Decimal('99')), delta=0.1)
		self.assertAlmostEqual(Decimal('34.7'), utils.calculate_dew_point(Decimal('55.7'), Decimal('45')), delta=0.1)

	def test_calculate_thw_index(self):
		self.assertIsNone(utils.calculate_thw_index(Decimal('69.9'), Decimal('90'), Decimal('5')))
		# TODO: More assertions

	@skip('This calculation is not complete.')
	def test_calculate_thsw_index(self):
		self.assertEqual(
			Decimal('0'),
			utils.calculate_thsw_index(Decimal('36.5'), 52, 1274, 0),
		)

	def test_calculate_cooling_degree_days(self):
		self.assertIsNone(utils.calculate_cooling_degree_days(Decimal('64.9')))
		self.assertIsNone(utils.calculate_cooling_degree_days(65))
		self.assertEqual(Decimal('0.1'), utils.calculate_cooling_degree_days(Decimal('65.1')))
		self.assertEqual(Decimal('18.5'), utils.calculate_cooling_degree_days(Decimal('83.5')))
		self.assertEqual(Decimal('25'), utils.calculate_cooling_degree_days(Decimal('90')))

	def test_calculate_heating_degree_days(self):
		self.assertIsNone(utils.calculate_heating_degree_days(Decimal('65.1')))
		self.assertIsNone(utils.calculate_heating_degree_days(65))
		self.assertEqual(Decimal('0.1'), utils.calculate_heating_degree_days(Decimal('64.9')))
		self.assertEqual(Decimal('39.6'), utils.calculate_heating_degree_days(Decimal('25.4')))
		self.assertEqual(Decimal('55'), utils.calculate_heating_degree_days(Decimal('10')))


class TestHighTenMinuteWindAverageCalculation(TestCase):

	def test_bogus_inputs_yield_empty_results(self):
		avg, direction, start, end = utils.calculate_10_minute_wind_average([])

		self.assertIsNone(avg)
		self.assertIsNone(direction)
		self.assertIsNone(start)
		self.assertIsNone(end)

		avg, direction, start, end = utils.calculate_10_minute_wind_average(())

		self.assertIsNone(avg)
		self.assertIsNone(direction)
		self.assertIsNone(start)
		self.assertIsNone(end)

		avg, direction, start, end = utils.calculate_10_minute_wind_average(
			[
				(1, 'NW', datetime(2016, 4, 29, 6, 5), 5, ),
				(1, 'NNW', datetime(2016, 4, 29, 6, 15), 10, ),
				(2, 'WNW', datetime(2016, 4, 29, 6, 26), 11, ),
				(1, 'NE', datetime(2016, 4, 29, 6, 27), 1, ),
			],
		)

		self.assertIsNone(avg)
		self.assertIsNone(direction)
		self.assertIsNone(start)
		self.assertIsNone(end)

	def test_10_minute_record_period(self):
		avg, direction, start, end = utils.calculate_10_minute_wind_average(
			[
				(1, 'NW', datetime(2016, 4, 29, 6, 10), 10, ),
				(1, 'NNW', datetime(2016, 4, 29, 6, 20), 10, ),
				(2, 'WNW', datetime(2016, 4, 29, 6, 30), 10, ),
				(1, 'NE', datetime(2016, 4, 29, 6, 40), 10, ),
			],
		)

		self.assertEqual(Decimal('2'), avg)
		self.assertEqual('WNW', direction)
		self.assertEqual(start, datetime(2016, 4, 29, 6, 21))
		self.assertEqual(end, datetime(2016, 4, 29, 6, 30))

		avg, direction, start, end = utils.calculate_10_minute_wind_average(
			(
				(Decimal('1'), 'NW', datetime(2016, 4, 29, 6, 10), Decimal('10'), ),
				(Decimal('1'), 'NNW', datetime(2016, 4, 29, 6, 20), Decimal('10'), ),
				(Decimal('2'), 'WNW', datetime(2016, 4, 29, 6, 30), Decimal('10'), ),
				(Decimal('1'), 'NE', datetime(2016, 4, 29, 6, 40), Decimal('10'), ),
			),
		)

		self.assertEqual(Decimal('2'), avg)
		self.assertEqual('WNW', direction)
		self.assertEqual(start, datetime(2016, 4, 29, 6, 21))
		self.assertEqual(end, datetime(2016, 4, 29, 6, 30))

	def test_5_minute_record_period(self):
		avg, direction, start, end = utils.calculate_10_minute_wind_average(
			[
				(1, 'NW', datetime(2016, 4, 29, 6, 5), 5, ),
				(1, 'NNW', datetime(2016, 4, 29, 6, 10), 5, ),
				(2, 'WNW', datetime(2016, 4, 29, 6, 15), 5, ),
				(1, 'NE', datetime(2016, 4, 29, 6, 20), 5, ),
			]
		)

		self.assertEqual(Decimal('1.5'), avg)
		self.assertEqual('NNW', direction)
		self.assertEqual(start, datetime(2016, 4, 29, 6, 6))
		self.assertEqual(end, datetime(2016, 4, 29, 6, 15))

	def test_2_minute_record_period(self):
		avg, direction, start, end = utils.calculate_10_minute_wind_average(
			[
				(1, 'NW', datetime(2016, 4, 29, 6, 2), 2, ),
				(1, 'NNW', datetime(2016, 4, 29, 6, 4), 2, ),
				(2, 'N', datetime(2016, 4, 29, 6, 6), 2, ),
				(1, 'NE', datetime(2016, 4, 29, 6, 8), 2, ),
				(3, 'NE', datetime(2016, 4, 29, 6, 10), 2, ),
				(1, 'N', datetime(2016, 4, 29, 6, 12), 2, ),
				(2, 'NE', datetime(2016, 4, 29, 6, 14), 2, ),
				(1, 'NNW', datetime(2016, 4, 29, 6, 16), 2, ),
				(1, 'NNW', datetime(2016, 4, 29, 6, 18), 2, ),
				(2, 'NNW', datetime(2016, 4, 29, 6, 20), 2, ),
			]
		)

		self.assertEqual(Decimal('1.8'), avg)
		self.assertEqual('NE', direction)
		self.assertEqual(start, datetime(2016, 4, 29, 6, 5))
		self.assertEqual(end, datetime(2016, 4, 29, 6, 14))

	def test_5_minute_record_actual_day_data(self):
		sample_wind_data = imp.load_source(
			'sample_wind_data',
			os.path.dirname(os.path.dirname(os.path.realpath(__file__))) + '/data/sample_day_wind_data_5_minute.py',
		)

		avg, direction, start, end = utils.calculate_10_minute_wind_average(
			[(s, d, datetime(*t), 5, ) for (s, d, t, ) in sample_wind_data.data]
		)

		self.assertEqual(Decimal('6.5'), avg)
		self.assertEqual('SSW', direction)
		self.assertEqual(start, datetime(2016, 4, 27, 12, 36))
		self.assertEqual(end, datetime(2016, 4, 27, 12, 45))

	def test_record_period_change(self):
		avg, direction, start, end = utils.calculate_10_minute_wind_average(
			[
				(1, 'NW', datetime(2016, 4, 29, 6, 10), 10, ),
				(5, 'NNW', datetime(2016, 4, 29, 6, 20), 10, ),
				(2, 'N', datetime(2016, 4, 29, 6, 25), 5, ),
				(1, 'NE', datetime(2016, 4, 29, 6, 30), 5, ),
				(3, 'NE', datetime(2016, 4, 29, 6, 35), 5, ),
				(1, 'N', datetime(2016, 4, 29, 6, 40), 5, ),
				(2, 'NE', datetime(2016, 4, 29, 6, 42), 2, ),
				(1, 'NNW', datetime(2016, 4, 29, 6, 44), 2, ),
				(1, 'NNW', datetime(2016, 4, 29, 6, 46), 2, ),
				(2, 'NNW', datetime(2016, 4, 29, 6, 48), 2, ),
			]
		)

		self.assertEqual(Decimal('5'), avg)
		self.assertEqual('NNW', direction)
		self.assertEqual(start, datetime(2016, 4, 29, 6, 11))
		self.assertEqual(end, datetime(2016, 4, 29, 6, 20))

		avg, direction, start, end = utils.calculate_10_minute_wind_average(
			[
				(1, 'NW', datetime(2016, 4, 29, 6, 10), 10, ),
				(2, 'NNW', datetime(2016, 4, 29, 6, 20), 10, ),
				(2, 'N', datetime(2016, 4, 29, 6, 25), 5, ),
				(1, 'NE', datetime(2016, 4, 29, 6, 30), 5, ),
				(3, 'NE', datetime(2016, 4, 29, 6, 35), 5, ),
				(1, 'N', datetime(2016, 4, 29, 6, 40), 5, ),
				(2, 'NE', datetime(2016, 4, 29, 6, 42), 2, ),
				(3, 'NNW', datetime(2016, 4, 29, 6, 44), 2, ),
				(2, 'NNW', datetime(2016, 4, 29, 6, 46), 2, ),
				(3, 'NNW', datetime(2016, 4, 29, 6, 48), 2, ),
			]
		)

		self.assertEqual(Decimal('2.2'), avg)
		self.assertEqual('NNW', direction)
		self.assertEqual(start, datetime(2016, 4, 29, 6, 39))
		self.assertEqual(end, datetime(2016, 4, 29, 6, 48))
