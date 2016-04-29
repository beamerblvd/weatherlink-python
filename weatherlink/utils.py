from __future__ import absolute_import

import collections
import decimal

"""
It is important that all of the math in this module takes place using decimal precision. Floating-point precision is
far too inaccurate and can cause errors of greater than plus/minus one degree in the results.
"""

ZERO = decimal.Decimal('0')
ONE = decimal.Decimal('1')
TWO = decimal.Decimal('2')
FOUR = decimal.Decimal('4')
FIVE = decimal.Decimal('5')
TEN = decimal.Decimal('10')
ONE_TENTH = decimal.Decimal('0.1')
ONE_HUNDREDTH = ONE_TENTH * ONE_TENTH
FIVE_NINTHS = decimal.Decimal('5.0') / decimal.Decimal('9.0')
NINE_FIFTHS = decimal.Decimal('9.0') / decimal.Decimal('5.0')

CELSIUS_CONSTANT = decimal.Decimal('32')
KELVIN_CONSTANT = decimal.Decimal('459.67')
KILOPASCAL_MERCURY_CONSTANT = decimal.Decimal('0.295299830714')
MILLIBAR_MERCURY_CONSTANT = KILOPASCAL_MERCURY_CONSTANT * ONE_TENTH
METERS_PER_SECOND_CONSTANT = decimal.Decimal('0.44704')

# Wet bulb constants used by NOAA/NWS in its wet bulb temperature charts
WB_0_00066 = decimal.Decimal('0.00066')
WB_0_007 = decimal.Decimal('0.007')
WB_0_114 = decimal.Decimal('0.114')
WB_0_117 = decimal.Decimal('0.117')
WB_2_5 = decimal.Decimal('2.5')
WB_6_11 = decimal.Decimal('6.11')
WB_7_5 = decimal.Decimal('7.5')
WB_14_55 = decimal.Decimal('14.55')
WB_15_9 = decimal.Decimal('15.9')
WB_237_7 = decimal.Decimal('237.7')

# Dew point constants used by NOAA/NWS in the August-Roche-Magnus approximation with the Bogel modification
DP_A = decimal.Decimal('6.112')  # millibars
DP_B = decimal.Decimal('17.67')  # no units
DP_C = decimal.Decimal('243.5')  # degrees Celsius
DP_D = decimal.Decimal('234.5')  # degrees Celsius

# Heat index constants used by NOAA/NWS in its heat index tables
HI_SECOND_FORMULA_THRESHOLD = decimal.Decimal('80.0')
HI_0_094 = decimal.Decimal('0.094')
HI_0_5 = decimal.Decimal('0.5')
HI_1_2 = decimal.Decimal('1.2')
HI_61_0 = decimal.Decimal('61.0')
HI_68_0 = decimal.Decimal('68.0')
HI_C1 = decimal.Decimal('-42.379')
HI_C2 = decimal.Decimal('2.04901523')
HI_C3 = decimal.Decimal('10.14333127')
HI_C4 = decimal.Decimal('-0.22475541')
HI_C5 = decimal.Decimal('-0.00683783')
HI_C6 = decimal.Decimal('-0.05481717')
HI_C7 = decimal.Decimal('0.00122874')
HI_C8 = decimal.Decimal('0.00085282')
HI_C9 = decimal.Decimal('-0.00000199')
HI_FIRST_ADJUSTMENT_THRESHOLD = (decimal.Decimal('80.0'), decimal.Decimal('112.0'), decimal.Decimal('13.0'), )
HI_13 = decimal.Decimal('13')
HI_17 = decimal.Decimal('17')
HI_95 = decimal.Decimal('95')
HI_SECOND_ADJUSTMENT_THRESHOLD = (decimal.Decimal('80.0'), decimal.Decimal('87.0'), decimal.Decimal('85.0'), )
HI_85 = decimal.Decimal('85')
HI_87 = decimal.Decimal('87')

# Wind chill constants used by NOAA/NWS in its wind chill tables
WC_C1 = decimal.Decimal('35.74')
WC_C2 = decimal.Decimal('0.6215')
WC_C3 = decimal.Decimal('35.75')
WC_C4 = decimal.Decimal('0.4275')
WC_V_EXP = decimal.Decimal('0.16')

# Constants used by Davis Instruments for its THW calculations
THW_INDEX_CONSTANT = decimal.Decimal('1.072')

# Constants used by the Australian Bureau of Meteorology for its apparent temperature (THSW) calculations
THSW_0_348 = decimal.Decimal('0.348')
THSW_0_70 = decimal.Decimal('0.70')
THSW_4_25 = decimal.Decimal('4.25')
THSW_6_105 = decimal.Decimal('6.105')
THSW_17_27 = decimal.Decimal('17.27')
THSW_237_7 = decimal.Decimal('237.7')

HEAT_INDEX_THRESHOLD = decimal.Decimal('70.0')  # degrees Fahrenheit
WIND_CHILL_THRESHOLD = decimal.Decimal('40.0')  # degrees Fahrenheit
DEGREE_DAYS_THRESHOLD = decimal.Decimal('65.0')  # degrees Fahrenheit


def _as_decimal(value):
	return value if isinstance(value, decimal.Decimal) else decimal.Decimal(value)


def convert_fahrenheit_to_kelvin(temperature):
	return (temperature + KELVIN_CONSTANT) * FIVE_NINTHS
assert convert_fahrenheit_to_kelvin(32) == decimal.Decimal('273.15')
assert convert_fahrenheit_to_kelvin(60).quantize(decimal.Decimal('0.01')) == decimal.Decimal('288.71')


def convert_kelvin_to_fahrenheit(temperature):
	return (temperature * NINE_FIFTHS) - KELVIN_CONSTANT
assert convert_kelvin_to_fahrenheit(convert_fahrenheit_to_kelvin(32)) == decimal.Decimal('32')
assert convert_kelvin_to_fahrenheit(convert_fahrenheit_to_kelvin(60)).quantize(decimal.Decimal('0.00000001')) == decimal.Decimal('60')


def convert_fahrenheit_to_celsius(temperature):
	return (temperature - CELSIUS_CONSTANT) * FIVE_NINTHS
assert convert_fahrenheit_to_celsius(32) == decimal.Decimal('0')
assert convert_fahrenheit_to_celsius(212) == decimal.Decimal('100')


def convert_celsius_to_fahrenheit(temperature):
	return (temperature * NINE_FIFTHS) + CELSIUS_CONSTANT
assert convert_celsius_to_fahrenheit(convert_fahrenheit_to_celsius(32)) == decimal.Decimal('32')
assert convert_celsius_to_fahrenheit(convert_fahrenheit_to_celsius(212)) == decimal.Decimal('212')


def convert_inches_of_mercury_to_kilopascals(barometric_pressure):
	return (barometric_pressure / KILOPASCAL_MERCURY_CONSTANT).quantize(ONE_HUNDREDTH)
assert convert_inches_of_mercury_to_kilopascals(1) == decimal.Decimal('3.39')
assert convert_inches_of_mercury_to_kilopascals(decimal.Decimal('29.45')) == decimal.Decimal('99.73')
assert convert_inches_of_mercury_to_kilopascals(30) == decimal.Decimal('101.59')


def convert_inches_of_mercury_to_millibars(barometric_pressure):
	return (barometric_pressure / MILLIBAR_MERCURY_CONSTANT).quantize(ONE_HUNDREDTH)
assert convert_inches_of_mercury_to_millibars(1) == decimal.Decimal('33.86')
assert convert_inches_of_mercury_to_millibars(decimal.Decimal('29.45')) == decimal.Decimal('997.29')
assert convert_inches_of_mercury_to_millibars(30) == decimal.Decimal('1015.92')


def convert_miles_per_hour_to_meters_per_second(wind_speed):
	return wind_speed * METERS_PER_SECOND_CONSTANT
assert convert_miles_per_hour_to_meters_per_second(1) == decimal.Decimal('0.44704')
assert convert_miles_per_hour_to_meters_per_second(13) == decimal.Decimal('5.81152')


def calculate_wet_bulb_temperature(temperature, relative_humidity, barometric_pressure):
	T = temperature
	RH = _as_decimal(relative_humidity)
	P = convert_inches_of_mercury_to_millibars(barometric_pressure)
	Tdc = (
		T - (WB_14_55 + WB_0_114 * T) * (1 - (ONE_HUNDREDTH * RH)) -
		((WB_2_5 + WB_0_007 * T) * (1 - (ONE_HUNDREDTH * RH))) ** 3 -
		(WB_15_9 + WB_0_117 * T) * (1 - (ONE_HUNDREDTH * RH)) ** 14
	)
	E = WB_6_11 * 10 ** (WB_7_5 * Tdc / (WB_237_7 + Tdc))
	return (
		(((WB_0_00066 * P) * T) + ((4098 * E) / ((Tdc + WB_237_7) ** 2) * Tdc)) / ((WB_0_00066 * P) + (4098 * E) / ((Tdc + WB_237_7) ** 2))
	).quantize(ONE_TENTH)
assert calculate_wet_bulb_temperature(decimal.Decimal('84.4'), decimal.Decimal('50'), decimal.Decimal('29.80')) == decimal.Decimal('69.4')
assert calculate_wet_bulb_temperature(decimal.Decimal('91.5'), decimal.Decimal('45'), decimal.Decimal('30.01')) == decimal.Decimal('73.4')
assert calculate_wet_bulb_temperature(decimal.Decimal('55.7'), decimal.Decimal('85'), decimal.Decimal('29.41')) == decimal.Decimal('52.8')


def _dew_point_gamma_m(T, RH):
	return (
		RH / 100 * (
			(DP_B - (T / DP_D)) * (T / (DP_C + T))
		).exp()
	).ln()


def calculate_dew_point(temperature, relative_humidity):
	T = convert_fahrenheit_to_celsius(temperature)
	RH = _as_decimal(relative_humidity)
	return convert_celsius_to_fahrenheit(
		(DP_C * _dew_point_gamma_m(T, RH)) / (DP_B - _dew_point_gamma_m(T, RH))
	).quantize(ONE_TENTH)
assert calculate_dew_point(decimal.Decimal('83.1'), decimal.Decimal('54')) == decimal.Decimal('64.4')
assert calculate_dew_point(decimal.Decimal('82.1'), decimal.Decimal('55')) == decimal.Decimal('64.0')
assert calculate_dew_point(decimal.Decimal('77.9'), decimal.Decimal('58')) == decimal.Decimal('61.7')
assert calculate_dew_point(decimal.Decimal('54.5'), decimal.Decimal('97')) == decimal.Decimal('53.6')
assert calculate_dew_point(decimal.Decimal('32.0'), decimal.Decimal('99')) == decimal.Decimal('31.8')
assert calculate_dew_point(decimal.Decimal('95.0'), decimal.Decimal('31')) == decimal.Decimal('59.2')


def _abs(d):
	return max(d, -d)


def calculate_heat_index(temperature, relative_humidity):
	if temperature < HEAT_INDEX_THRESHOLD:
		return None

	T = temperature
	RH = _as_decimal(relative_humidity)

	# Formulas and constants taken from http://www.wpc.ncep.noaa.gov/html/heatindex_equation.shtml
	heat_index = HI_0_5 * (T + HI_61_0 + ((T - HI_68_0) * HI_1_2) + (RH * HI_0_094))
	heat_index = (heat_index + T) / TWO  # This is the average

	if heat_index < HI_SECOND_FORMULA_THRESHOLD:
		return heat_index.quantize(ONE_TENTH, rounding=decimal.ROUND_UP)

	heat_index = (
		HI_C1 + (HI_C2 * T) + (HI_C3 * RH) + (HI_C4 * T * RH) + (HI_C5 * T * T) +
		(HI_C6 * RH * RH) + (HI_C7 * T * T * RH) + (HI_C8 * T * RH * RH) + (HI_C9 * T * T * RH * RH)
	)

	if (HI_FIRST_ADJUSTMENT_THRESHOLD[0] <= T <= HI_FIRST_ADJUSTMENT_THRESHOLD[1]
		and RH < HI_FIRST_ADJUSTMENT_THRESHOLD[2]):
		heat_index -= (
			((HI_13 - RH) / FOUR) * ((HI_17 - _abs(T - HI_95)) / HI_17).sqrt()
		)
	elif (HI_SECOND_ADJUSTMENT_THRESHOLD[0] <= T <= HI_SECOND_ADJUSTMENT_THRESHOLD[1]
		and RH > HI_SECOND_ADJUSTMENT_THRESHOLD[2]):
		heat_index += (
			((RH - HI_85) / TEN) * ((HI_87 - T) / FIVE)
		)

	return heat_index.quantize(ONE_TENTH, rounding=decimal.ROUND_UP)
assert calculate_heat_index(decimal.Decimal('69.9'), decimal.Decimal('90')) == None
assert calculate_heat_index(decimal.Decimal('80'), decimal.Decimal('40')) == decimal.Decimal('79.8')
assert calculate_heat_index(decimal.Decimal('81.5'), decimal.Decimal('58')) == decimal.Decimal('83.5')
assert calculate_heat_index(decimal.Decimal('80'), decimal.Decimal('100')) == decimal.Decimal('89.3')
assert calculate_heat_index(decimal.Decimal('100'), decimal.Decimal('65')) == decimal.Decimal('135.9')
assert calculate_heat_index(decimal.Decimal('70.0'), decimal.Decimal('5')) == decimal.Decimal('68.5')
assert calculate_heat_index(decimal.Decimal('70.2'), decimal.Decimal('5')) == decimal.Decimal('68.7')
assert calculate_heat_index(decimal.Decimal('70.1'), decimal.Decimal('86')) == decimal.Decimal('70.5')
assert calculate_heat_index(decimal.Decimal('70.1'), decimal.Decimal('42.5')) == decimal.Decimal('69.5')
assert calculate_heat_index(decimal.Decimal('70.1'), decimal.Decimal('25')) == decimal.Decimal('69.1')
assert calculate_heat_index(decimal.Decimal('80'), decimal.Decimal('86')) == decimal.Decimal('85.3')
assert calculate_heat_index(decimal.Decimal('86'), decimal.Decimal('90')) == decimal.Decimal('105.4')
assert calculate_heat_index(decimal.Decimal('95'), decimal.Decimal('12')) == decimal.Decimal('90.1')
assert calculate_heat_index(decimal.Decimal('111'), decimal.Decimal('12')) == decimal.Decimal('107.0')


def calculate_wind_chill(temperature, wind_speed):
	if temperature > WIND_CHILL_THRESHOLD:
		return None

	T = temperature
	WS = _as_decimal(wind_speed)

	if WS == ZERO:  # No wind results in no chill, so skip it
		return T

	V = WS ** WC_V_EXP
	wind_chill = (
		WC_C1 + (WC_C2 * T) - (WC_C3 * V) + (WC_C4 * T * V)
	).quantize(ONE_TENTH)

	return T if wind_chill > T else wind_chill
assert calculate_wind_chill(decimal.Decimal('40.1'), decimal.Decimal('5')) == None
assert calculate_wind_chill(decimal.Decimal('40.0'), decimal.Decimal('5')) == decimal.Decimal('36.5')
assert calculate_wind_chill(decimal.Decimal('40.0'), decimal.Decimal('45')) == decimal.Decimal('26.3')
assert calculate_wind_chill(decimal.Decimal('0'), decimal.Decimal('5')) == decimal.Decimal('-10.5')
assert calculate_wind_chill(decimal.Decimal('0'), decimal.Decimal('45')) == decimal.Decimal('-30.0')
assert calculate_wind_chill(decimal.Decimal('39.9'), decimal.Decimal('0')) == decimal.Decimal('39.9')
assert calculate_wind_chill(decimal.Decimal('39.9'), decimal.Decimal('2')) == decimal.Decimal('39.7')
assert calculate_wind_chill(decimal.Decimal('39.9'), decimal.Decimal('3')) == decimal.Decimal('38.3')


def calculate_thw_index(temperature, relative_humidity, wind_speed):
	hi = calculate_heat_index(temperature, relative_humidity)
	WS = _as_decimal(wind_speed)
	if not hi:
		return None
	return (
		hi - (THW_INDEX_CONSTANT * WS).quantize(ONE_TENTH, rounding=decimal.ROUND_DOWN)
	)
assert calculate_thw_index(decimal.Decimal('69.9'), decimal.Decimal('90'), decimal.Decimal('5')) == None


def calculate_thsw_index(temperature, relative_humidity, solar_radiation, wind_speed):
	T = convert_fahrenheit_to_celsius(temperature)
	RH = _as_decimal(relative_humidity)
	WS = convert_miles_per_hour_to_meters_per_second(_as_decimal(wind_speed))
	E = RH / 100 * THSW_6_105 * (THSW_17_27 * T / ( THSW_237_7 + T )).exp()
	Thsw = T + (THSW_0_348 * E) - (THSW_0_70 * WS) + THSW_0_70 * (solar_radiation / (WS + 10)) - THSW_4_25
	return convert_celsius_to_fahrenheit(Thsw).quantize(ONE_TENTH)


def calculate_cooling_degree_days(average_temperature):
	if average_temperature <= DEGREE_DAYS_THRESHOLD:
		return None
	return average_temperature - DEGREE_DAYS_THRESHOLD
assert calculate_cooling_degree_days(DEGREE_DAYS_THRESHOLD - 1) == None
assert calculate_cooling_degree_days(DEGREE_DAYS_THRESHOLD) == None
assert calculate_cooling_degree_days(DEGREE_DAYS_THRESHOLD + 1) == ONE
assert calculate_cooling_degree_days(decimal.Decimal('90')) == decimal.Decimal('25')


def calculate_heating_degree_days(average_temperature):
	if average_temperature >= DEGREE_DAYS_THRESHOLD:
		return None
	return DEGREE_DAYS_THRESHOLD - average_temperature
assert calculate_heating_degree_days(DEGREE_DAYS_THRESHOLD + 1) == None
assert calculate_heating_degree_days(DEGREE_DAYS_THRESHOLD) == None
assert calculate_heating_degree_days(DEGREE_DAYS_THRESHOLD - 1) == ONE
assert calculate_heating_degree_days(decimal.Decimal('10')) == decimal.Decimal('55')


def calculate_10_minute_wind_average(records, record_minute_span):
	# Yes, we want integer division here
	# This is the maximum number of whole records that can fit in a 10-minute span
	# It's only valid if the archive record minute span is 10 minutes or less
	wind_records_to_include = 10 / record_minute_span
	if wind_records_to_include == 0:
		return None, None, None, None

	speed_queue = collections.deque(maxlen=wind_records_to_include)
	direction_queue = collections.deque(maxlen=wind_records_to_include)
	timestamp_queue = collections.deque(maxlen=wind_records_to_include)
	current_max = ZERO
	current_direction_list = []
	current_timestamp_list = []

	for (wind_speed, wind_speed_direction, timestamp_station, ) in records:
		wind_speed = _as_decimal(wind_speed)
		speed_queue.append(wind_speed)
		direction_queue.append(wind_speed_direction)
		timestamp_queue.append(timestamp_station)

		if len(speed_queue) == wind_records_to_include:
			# This is the rolling average of the last 10 minutes
			average = sum(speed_queue) / wind_records_to_include
			if average > current_max:
				current_max = average
				current_direction_list = list(direction_queue)
				current_timestamp_list = list(timestamp_queue)

	if current_max > ZERO:
		wind_speed_high_10_minute_average = current_max

		wind_speed_high_10_minute_average_direction = None
		wind_speed_high_10_minute_average_start = None
		wind_speed_high_10_minute_average_end = None

		if current_direction_list:
			count = collections.Counter(current_direction_list)
			wind_speed_high_10_minute_average_direction = count.most_common()[0][0]

		if current_timestamp_list:
			wind_speed_high_10_minute_average_start = current_timestamp_list[0]
			wind_speed_high_10_minute_average_end = current_timestamp_list[-1]

		return (
			wind_speed_high_10_minute_average,
			wind_speed_high_10_minute_average_direction,
			wind_speed_high_10_minute_average_start,
			wind_speed_high_10_minute_average_end,
		)

	return None, None, None, None
assert (
	calculate_10_minute_wind_average([], 5)
	== (None, None, None, None, )
)
assert (
	calculate_10_minute_wind_average([(1, 'NW', 10, ), (1, 'NNW', 11, ), (2, 'WNW', 12, ), (1, 'NE', 13, )], 11)
	== (None, None, None, None, )
)
assert (
	calculate_10_minute_wind_average([(1, 'NW', 10, ), (1, 'NNW', 11, ), (2, 'WNW', 12, ), (1, 'NE', 13, )], 10)
	== (decimal.Decimal('2'), 'WNW', 12, 12, )
)
assert (
	calculate_10_minute_wind_average([(1, 'NW', 10, ), (1, 'NNW', 11, ), (2, 'WNW', 12, ), (1, 'NE', 13, )], 5)
	== (decimal.Decimal('1.5'), 'NNW', 11, 12, )
)
assert (
	(
		calculate_10_minute_wind_average(
			[
				(1, 'NW', 10, ),
				(1, 'NNW', 11, ),
				(2, 'N', 12, ),
				(1, 'NE', 13, ),
				(3, 'NE', 14, ),
				(1, 'N', 15, ),
				(2, 'NE', 16, ),
				(1, 'NNW', 17, ),
				(1, 'NNW', 18, ),
				(2, 'NNW', 19, ),
			],
			2
		)
	) == (decimal.Decimal('1.8'), 'NE', 12, 16, )
)


def _append_to_list(l, v):
	if v:
		l.append(v)


def calculate_all_record_values(record, record_minute_span_default=30):
	arguments = {}

	wind_speed = _as_decimal(record.get('wind_speed'))
	wind_speed_high = record.get('wind_speed_high')
	humidity_outside = record.get('humidity_outside')
	humidity_inside = record.get('humidity_inside')
	barometric_pressure = record.get('barometric_pressure')
	temperature_outside = record.get('temperature_outside')
	temperature_outside_low = record.get('temperature_outside_low')
	temperature_outside_high = record.get('temperature_outside_high')
	temperature_inside = record.get('temperature_inside')
	solar_radiation = record.get('solar_radiation')
	solar_radiation_high = record.get('solar_radiation_high')

	minutes_covered = (record.get('minutes_covered', record_minute_span_default) or record_minute_span_default)
	if wind_speed and minutes_covered:
		ws_mpm = wind_speed / 60
		distance = ws_mpm * minutes_covered
		arguments['wind_run_distance_total'] = distance

	if humidity_outside and barometric_pressure:
		if temperature_outside:
			a = calculate_wet_bulb_temperature(temperature_outside, humidity_outside, barometric_pressure)
			if a:
				arguments['temperature_wet_bulb'] = a
		if temperature_outside_low:
			a = calculate_wet_bulb_temperature(temperature_outside_low, humidity_outside, barometric_pressure)
			if a:
				arguments['temperature_wet_bulb_low'] = a
		if temperature_outside_high:
			a = calculate_wet_bulb_temperature(temperature_outside_high, humidity_outside, barometric_pressure)
			if a:
				arguments['temperature_wet_bulb_high'] = a

	if humidity_outside:
		a = []
		b = []
		if temperature_outside:
			_append_to_list(a, calculate_dew_point(temperature_outside, humidity_outside))
			_append_to_list(b, calculate_heat_index(temperature_outside, humidity_outside))
		if temperature_outside_low:
			_append_to_list(a, calculate_dew_point(temperature_outside_low, humidity_outside))
			_append_to_list(b, calculate_heat_index(temperature_outside_low, humidity_outside))
		if temperature_outside_high:
			_append_to_list(a, calculate_dew_point(temperature_outside_high, humidity_outside))
			_append_to_list(b, calculate_heat_index(temperature_outside_high, humidity_outside))
		if a:
			arguments['dew_point_outside'] = a[0]
			arguments['dew_point_outside_low'] = min(a)
			arguments['dew_point_outside_high'] = max(a)
		if b:
			arguments['heat_index_outside'] = b[0]
			arguments['heat_index_outside_low'] = min(b)
			arguments['heat_index_outside_high'] = max(b)

	if humidity_inside and temperature_inside:
		a = calculate_dew_point(temperature_inside, humidity_inside)
		b = calculate_heat_index(temperature_inside, humidity_inside)
		if a:
			arguments['dew_point_inside'] = a
		if b:
			arguments['heat_index_inside'] = b

	if (wind_speed or wind_speed_high) and (temperature_outside or temperature_outside_high or temperature_outside_low):
		a = []
		if wind_speed and temperature_outside:
			_append_to_list(a, calculate_wind_chill(temperature_outside, wind_speed))
		if wind_speed and temperature_outside_high:
			_append_to_list(a, calculate_wind_chill(temperature_outside_high, wind_speed))
		if wind_speed and temperature_outside_low:
			_append_to_list(a, calculate_wind_chill(temperature_outside_low, wind_speed))
		if wind_speed_high and temperature_outside:
			_append_to_list(a, calculate_wind_chill(temperature_outside, wind_speed_high))
		if wind_speed_high and temperature_outside_high:
			_append_to_list(a, calculate_wind_chill(temperature_outside_high, wind_speed_high))
		if wind_speed_high and temperature_outside_low:
			_append_to_list(a, calculate_wind_chill(temperature_outside_low, wind_speed_high))
		if a:
			arguments['wind_chill'] = a[0]
			arguments['wind_chill_low'] = min(a)
			arguments['wind_chill_high'] = max(a)

	if humidity_outside and (temperature_outside or temperature_outside_high or temperature_outside_low):
		ws = wind_speed if wind_speed else 0
		wsh = wind_speed_high if wind_speed_high else 0

		a = []
		if temperature_outside:
			_append_to_list(a, calculate_thw_index(temperature_outside, humidity_outside, ws))
			_append_to_list(a, calculate_thw_index(temperature_outside, humidity_outside, wsh))
		if temperature_outside_high:
			_append_to_list(a, calculate_thw_index(temperature_outside_high, humidity_outside, ws))
			_append_to_list(a, calculate_thw_index(temperature_outside_high, humidity_outside, wsh))
		if temperature_outside_low:
			_append_to_list(a, calculate_thw_index(temperature_outside_low, humidity_outside, ws))
			_append_to_list(a, calculate_thw_index(temperature_outside_low, humidity_outside, wsh))
		if a:
			arguments['thw_index'] = a[0]
			arguments['thw_index_low'] = min(a)
			arguments['thw_index_high'] = max(a)

		if solar_radiation or solar_radiation_high:
			a = []
			if temperature_outside and solar_radiation:
				_append_to_list(a, calculate_thsw_index(temperature_outside, humidity_outside, solar_radiation, ws))
				_append_to_list(a, calculate_thsw_index(temperature_outside, humidity_outside, solar_radiation, wsh))
			if temperature_outside_high and solar_radiation:
				_append_to_list(a, calculate_thsw_index(temperature_outside_high, humidity_outside, solar_radiation, ws))
				_append_to_list(a, calculate_thsw_index(temperature_outside_high, humidity_outside, solar_radiation, wsh))
			if temperature_outside_low and solar_radiation:
				_append_to_list(a, calculate_thsw_index(temperature_outside_low, humidity_outside, solar_radiation, ws))
				_append_to_list(a, calculate_thsw_index(temperature_outside_low, humidity_outside, solar_radiation, wsh))
			if temperature_outside and solar_radiation_high:
				_append_to_list(a, calculate_thsw_index(temperature_outside, humidity_outside, solar_radiation_high, ws))
				_append_to_list(a, calculate_thsw_index(temperature_outside, humidity_outside, solar_radiation_high, wsh))
			if temperature_outside_high and solar_radiation_high:
				_append_to_list(a, calculate_thsw_index(temperature_outside_high, humidity_outside, solar_radiation_high, ws))
				_append_to_list(a, calculate_thsw_index(temperature_outside_high, humidity_outside, solar_radiation_high, wsh))
			if temperature_outside_low and solar_radiation_high:
				_append_to_list(a, calculate_thsw_index(temperature_outside_low, humidity_outside, solar_radiation_high, ws))
				_append_to_list(a, calculate_thsw_index(temperature_outside_low, humidity_outside, solar_radiation_high, wsh))
			if a:
				arguments['thsw_index'] = a[0]
				arguments['thsw_index_low'] = min(a)
				arguments['thsw_index_high'] = max(a)

	return arguments
