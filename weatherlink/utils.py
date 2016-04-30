"""
This module contains a series of important utilities that determine derived weather values from physical weather
measurements. In addition to calculations for wet bulb temperature, dew point, heat index, wind chill,
THW/THSW indexes, heating and cooling degree days, and high 10-minute wind average, it also includes conversion
functions for various units of temperature, barometric pressure, and wind speed.

It is important that all of the math in this module takes place using decimal precision. Floating-point precision is
far too inaccurate and can cause errors of greater than plus/minus one degree in the results. As such, the first
~100 lines of the code contain dozens of constants used in the aforementioned calculations. These constants come from
documents published by NOAA / the National Weather Service of the United States of America, Davis Instruments,
the Australian Bureau of Meteorology, and public domain imperial/SI conversion algorithms. Where possible/applicable,
the source of algorithms and the constants they use are cited within the algorithm (not with the constants).

Note that naming conventions for constants and variables in this module are non-standard, and in some cases violate
PEP8. This is intentional. Where a constant is defined in an official algorithm as a letter with a subscript number,
it is defined in this module as the abbreviation of the purpose, followed by an underscore, followed by the constant
name in the official algorithm. For example, the major heat index algorithm defines constants c1, c2, c3, ... c9. They
are defined in this module as `HI_C1`, `HI_C2`, `HI_C3`, ... `HI_C9`. Where a constant is used as a literal within
an algorithm, it is defined in this module as the abbreviation of the purpose, followed by an underscore, followed by
the numbers before the decimal point, optionally followed by an underscored and the numbers after the decimal point.
These shorter names help the code-defined constants more closely match the names used in the algorithms and also keeps
the code short and readable for the long and complex algorithms used in this module.

Some common constants used by multiple algorithms are defined at the top of the module as the English spelling of the
numeric value. A handful of other simpler constants are defined with standard, useful names.

In some of the functions, the local variables are defined as one- or two-letter uppercase variables, in violation of
PEP8. This is done so that the variables match those variables used in the official algorithms, in order to make the
code more readable.
"""

from __future__ import absolute_import

import collections
import datetime
import decimal


ZERO = decimal.Decimal('0')
ONE = decimal.Decimal('1')
TWO = decimal.Decimal('2')
FOUR = decimal.Decimal('4')
FIVE = decimal.Decimal('5')
TEN = decimal.Decimal('10')
ONE_TENTH = decimal.Decimal('0.1')
ONE_HUNDREDTH = ONE_TENTH * ONE_TENTH
ONE_THOUSANDTH = ONE_TENTH * ONE_HUNDREDTH
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
	"""
	Converts the value to a `Decimal` if it is not already, or returns the existing value if it is a `Decimal`, or
	returns `Decimal(0)` if the existing value is `None`.

	:param value: The value to cast/convert
	:type value: int | long | decimal.Decimal | NoneType

	:return: The value as a `Decimal`
	:rtype: decimal.Decimal
	"""
	return value if isinstance(value, decimal.Decimal) else decimal.Decimal(value or '0')


def convert_fahrenheit_to_kelvin(temperature):
	"""
	Converts the temperature from degrees Fahrenheit to Kelvin.

	:param temperature: The value to convert, which must be in degrees Fahrenheit
	:type temperature: int | long | decimal.Decimal

	:return: The temperature in Kelvin to three decimal places
	:rtype: decimal.Decimal
	"""
	return ((temperature + KELVIN_CONSTANT) * FIVE_NINTHS).quantize(ONE_THOUSANDTH)


def convert_kelvin_to_fahrenheit(temperature):
	"""
	Converts the temperature from Kelvin to degrees Fahrenheit.

	:param temperature: The value to convert, which must be in Kelvin
	:type temperature: int | long | decimal.Decimal

	:return: The temperature in degrees Fahrenheit to three decimal places
	:rtype: decimal.Decimal
	"""
	return ((temperature * NINE_FIFTHS) - KELVIN_CONSTANT).quantize(ONE_THOUSANDTH)


def convert_fahrenheit_to_celsius(temperature):
	"""
	Converts the temperature from degrees Fahrenheit to degrees Celsius.

	:param temperature: The value to convert, which must be in degrees Fahrenheit
	:type temperature: int | long | decimal.Decimal

	:return: The temperature in degrees Celsius to three decimal places
	:rtype: decimal.Decimal
	"""
	return ((temperature - CELSIUS_CONSTANT) * FIVE_NINTHS).quantize(ONE_THOUSANDTH)


def convert_celsius_to_fahrenheit(temperature):
	"""
	Converts the temperature from degrees Celsius to degrees Fahrenheit.

	:param temperature: The value to convert, which must be in degrees Celsius
	:type temperature: int | long | decimal.Decimal
	:return: The temperature in degrees Fahrenheit to three decimal places
	:rtype: decimal.Decimal
	"""
	return ((temperature * NINE_FIFTHS) + CELSIUS_CONSTANT).quantize(ONE_THOUSANDTH)


def convert_inches_of_mercury_to_kilopascals(barometric_pressure):
	"""
	Converts pressure measurements from inches of mercury (inHg) to kilopascals (kPa).

	:param barometric_pressure: The value to convert, which must be in inches of mercury
	:type barometric_pressure: int | long | decimal.Decimal
	:return: The pressure in kilopascals to two decimal places
	:rtype: decimal.Decimal
	"""
	return (barometric_pressure / KILOPASCAL_MERCURY_CONSTANT).quantize(ONE_HUNDREDTH)


def convert_inches_of_mercury_to_millibars(barometric_pressure):
	"""
	Converts pressure measurements from inches of mercury (inHg) to millibars (mb/mbar), also known as
	hectopascals (hPa).

	:param barometric_pressure: The value to convert, which must be in inches of mercury
	:type barometric_pressure: int | long | decimal.Decimal
	:return: The pressure in millibars (hectopascals) to two decimal places
	:rtype: decimal.Decimal
	"""
	return (barometric_pressure / MILLIBAR_MERCURY_CONSTANT).quantize(ONE_HUNDREDTH)


def convert_miles_per_hour_to_meters_per_second(wind_speed):
	"""
	Converts speed from miles per hour (MPH) to meters per second (m/s).

	:param wind_speed: The value to convert, which must be in miles per hour
	:type wind_speed: int | long | decimal.Decimal
	:return: The speed in meters per second to five decimal places
	:rtype: decimal.Decimal
	"""
	return (wind_speed * METERS_PER_SECOND_CONSTANT).quantize(METERS_PER_SECOND_CONSTANT)


def calculate_wet_bulb_temperature(temperature, relative_humidity, barometric_pressure):
	"""
	Uses the temperature, relative humidity, and barometric pressure to calculate the wet bulb temperature, which is
	"the temperature a parcel of air would have if it were cooled to saturation (100% relative humidity) by the
	evaporation of water into it." A wet bulb temperature above 80F (27C) is considered uncomfortable, while a wet
	bulb temperature above 95F (35C) is deadly, as it is beyond the threshold at which the human body can cool itself
	and starts absorbing heat from the surrounding environment. The citation comes from
	https://en.wikipedia.org/wiki/Wet-bulb_temperature. The algorithm used and its constants are sourced from
	http://www.aprweather.com/pages/calc.htm. In this algorithm:

	Tc is the temperature in degrees Celsius
	RH is the relative humidity percentage
	P is the atmospheric pressure in millibars
	Tdc is the dew point temperature for this algorithm (may not match the output of `calculate_dew_point`)
	E is the vapor pressure
	Tw is the wet bulb temperature in degrees Celsius

	:param temperature: The temperature in degrees Fahrenheit
	:type temperature: int | long | decimal.Decimal
	:param relative_humidity: The relative humidity expressed as a percentage (88.2 instead of 0.882)
	:type relative_humidity: int | long | decimal.Decimal
	:param barometric_pressure: The atmospheric pressure in inches of mercury
	:type barometric_pressure: int | long | decimal.Decimal

	:return: The wet bulb temperature in degrees Fahrenheit to one decimal place
	:rtype: decimal.Decimal
	"""
	Tc = convert_fahrenheit_to_celsius(temperature)
	RH = _as_decimal(relative_humidity)
	P = convert_inches_of_mercury_to_millibars(barometric_pressure)

	Tdc = (
		Tc - (WB_14_55 + WB_0_114 * Tc) * (1 - (ONE_HUNDREDTH * RH)) -
		((WB_2_5 + WB_0_007 * Tc) * (1 - (ONE_HUNDREDTH * RH))) ** 3 -
		(WB_15_9 + WB_0_117 * Tc) * (1 - (ONE_HUNDREDTH * RH)) ** 14
	)
	E = WB_6_11 * 10 ** (WB_7_5 * Tdc / (WB_237_7 + Tdc))
	Tw = (
		(((WB_0_00066 * P) * Tc) + ((4098 * E) / ((Tdc + WB_237_7) ** 2) * Tdc)) /
		((WB_0_00066 * P) + (4098 * E) / ((Tdc + WB_237_7) ** 2))
	)

	return convert_celsius_to_fahrenheit(Tw).quantize(ONE_TENTH)


def calculate_dew_point(temperature, relative_humidity):
	"""
	Uses the temperature and relative humidity to calculate the dew point, a measure of atmospheric moisture that is
	the temperature at which dew forms. "It is the temperature to which air must be cooled at constant pressure and
	water content to reach saturation." A dew point greater than 68F is considered high, while 72F is uncomfortable.
	A dew point of 80F or higher can often be deadly for asthma sufferers. In this algorithm:

	Tc is the temperature in degrees Celsius
	RH is the relative humidity percentage
	Tdc is the dew point temperature

	:param temperature: The temperature in degrees Fahrenheit
	:type temperature: int | long | decimal.Decimal
	:param relative_humidity: The relative humidity as a percentage (88.2 instead of 0.882)
	:type relative_humidity: int | long | decimal.Decimal

	:return: The dew point temperature in degrees Fahrenheit to one decimal place
	:rtype: decimal.Decimal
	"""
	Tc = convert_fahrenheit_to_celsius(temperature)
	RH = _as_decimal(relative_humidity)

	Ym = (
		RH / 100 * (
			(DP_B - (Tc / DP_D)) * (Tc / (DP_C + Tc))
		).exp()
	).ln()
	Tdc = (DP_C * Ym) / (DP_B - Ym)

	return convert_celsius_to_fahrenheit(Tdc).quantize(ONE_TENTH)


def _abs(d):
	return max(d, -d)


def calculate_heat_index(temperature, relative_humidity):
	"""
	Uses the temperature and relative humidity to calculate the heat index, the purpose of which is to represent a
	"felt-air temperature" close to what a human actually feels given the temperature and humidity. This index does
	not take into account the wind speed or solar radiation, and so is not the most accurate measure of a true
	"feels-like" temperature. For that, see `calculate_thw_index` and `calculate_thsw_index`. The algorithm used and
	its constants are sourced from http://www.wpc.ncep.noaa.gov/html/heatindex_equation.shtml. In this algorithm:

	T is the temperature in degrees Fahrenheit
	RH is the relative humidity percentage

	This function is tested against the NOAA/NWS heat index chart found at
	http://www.nws.noaa.gov/os/heat/heat_index.shtml. It returns `None` if the input temperature is less than 70F.
	Experts disagree as to whether the heat index is applicable between 70F and 80F, but this function returns a heat
	index calculation for those values.

	:param temperature: The temperature in degrees Fahrenheit
	:type temperature: int | long | decimal.Decimal
	:param relative_humidity: The relative humidity as a percentage (88.2 instead of 0.882)
	:type relative_humidity: int | long | decimal.Decimal

	:return: The heat index temperature in degrees Fahrenheit to one decimal place, or `None` if the temperature is
				less than 70F
	:rtype: decimal.Decimal
	"""
	if temperature < HEAT_INDEX_THRESHOLD:
		return None

	T = temperature
	RH = _as_decimal(relative_humidity)

	heat_index = HI_0_5 * (T + HI_61_0 + ((T - HI_68_0) * HI_1_2) + (RH * HI_0_094))
	heat_index = (heat_index + T) / TWO  # This is the average

	if heat_index < HI_SECOND_FORMULA_THRESHOLD:
		return heat_index.quantize(ONE_TENTH, rounding=decimal.ROUND_CEILING)

	heat_index = (
		HI_C1 + (HI_C2 * T) + (HI_C3 * RH) + (HI_C4 * T * RH) + (HI_C5 * T * T) +
		(HI_C6 * RH * RH) + (HI_C7 * T * T * RH) + (HI_C8 * T * RH * RH) + (HI_C9 * T * T * RH * RH)
	)

	if (HI_FIRST_ADJUSTMENT_THRESHOLD[0] <= T <= HI_FIRST_ADJUSTMENT_THRESHOLD[1] and
				RH < HI_FIRST_ADJUSTMENT_THRESHOLD[2]):
		heat_index -= (
			((HI_13 - RH) / FOUR) * ((HI_17 - _abs(T - HI_95)) / HI_17).sqrt()
		)
	elif (HI_SECOND_ADJUSTMENT_THRESHOLD[0] <= T <= HI_SECOND_ADJUSTMENT_THRESHOLD[1] and
							RH > HI_SECOND_ADJUSTMENT_THRESHOLD[2]):
		heat_index += (
			((RH - HI_85) / TEN) * ((HI_87 - T) / FIVE)
		)

	return heat_index.quantize(ONE_TENTH, rounding=decimal.ROUND_CEILING)


def calculate_wind_chill(temperature, wind_speed):
	"""
	Uses the air temperature and wind speed to calculate the wind chill, the purpose of which is to represent a
	"felt-air temperature" close to what a human actually feels given the temperature and wind speed. This index does
	not take into account the humidity or solar radiation, and so is not the most accurate measure of a true
	"feels-like" temperature. For that, see `calculate_thw_index` and `calculate_thsw_index`. The algorithm used and
	its constants are sourced from the chart at http://www.srh.noaa.gov/ssd/html/windchil.htm, and the function is
	tested against the same chart. In this algorithm:

	T is the temperature in degrees Fahrenheit
	WS is the wind speed in miles per hour

	This function returns `None` if the input temperature is above 40F.

	:param temperature: The temperature in degrees Fahrenheit
	:type temperature: int | long | decimal.Decimal
	:param wind_speed: The wind speed in miles per hour
	:type wind_speed: int | long | decimal.Decimal

	:return: The wind chill temperature in degrees Fahrenheit to one decimal place, or `None` if the temperature is
				higher than 40F
	:rtype: decimal.Decimal
	"""
	if temperature > WIND_CHILL_THRESHOLD:
		return None

	T = temperature
	WS = _as_decimal(wind_speed)

	if WS == ZERO:  # No wind results in no chill, so skip it
		return T

	V = WS ** WC_V_EXP
	wind_chill = (
		WC_C1 + (WC_C2 * T) - (WC_C3 * V) + (WC_C4 * T * V)
	).quantize(ONE_TENTH, rounding=decimal.ROUND_FLOOR)

	return T if wind_chill > T else wind_chill


def calculate_thw_index(temperature, relative_humidity, wind_speed):
	"""
	Uses the air temperature, relative humidity, and wind speed (THW = temperature-humidity-wind) to calculate a
	potentially more accurate "felt-air temperature." This is not as accurate, however, as the THSW index, which
	can only be calculated when solar radiation information is available. It uses `calculate_heat_index` and then
	applies additional calculations to it using the wind speed. As such, it returns `None` for input temperatures below
	70 degrees Fahrenheit. The additional calculations come from web forums rumored to contain the proprietary
	Davis Instruments THW index formulas.

	hi is the heat index as calculated by `calculate_heat_index`
	WS is the wind speed in miles per hour

	:param temperature: The temperature in degrees Fahrenheit
	:type temperature: int | long | decimal.Decimal
	:param relative_humidity: The relative humidity as a percentage (88.2 instead of 0.882)
	:type relative_humidity: int | long | decimal.Decimal
	:param wind_speed: The wind speed in miles per hour
	:type wind_speed: int | long | decimal.Decimal

	:return: The THW index temperature in degrees Fahrenheit to one decimal place, or `None` if the temperature is
				less than 70F
	:rtype: decimal.Decimal
	"""
	hi = calculate_heat_index(temperature, relative_humidity)
	WS = _as_decimal(wind_speed)

	if not hi:
		return None
	return hi - (THW_INDEX_CONSTANT * WS).quantize(ONE_TENTH, rounding=decimal.ROUND_CEILING)


def calculate_thsw_index(temperature, relative_humidity, solar_radiation, wind_speed):
	"""
	Uses the air temperature, relative humidity, solar radiation, and wind speed (THSW = temperature-humidity-sun-wind)
	to calculate a potentially more accurate "felt-air temperature." Given that it uses all the variables that affect
	how the human body perceives temperature, it is likely the most accurate measure of a true "feels like" temperature.
	It is applied to all temperatures, high and low. Though named to mimic the THSW index from Davis Instruments, the
	algorithm comes from the Australian Bureau of Meteorology. In this algorithm:

	Tc is the temperature in degrees Celsius
	RH is the relative humidity percentage
	WS is the wind speed in meters per second
	E is the vapor pressure
	Thsw is the THSW index temperature

	:param temperature: The temperature in degrees Fahrenheit
	:type temperature: int | long | decimal.Decimal
	:param relative_humidity: The relative humidity as a percentage (88.2 instead of 0.882)
	:type relative_humidity: int | long | decimal.Decimal
	:param solar_radiation: The absorbed solar radiation in watts per square meter
	:type solar_radiation: int | long | decimal.Decimal
	:param wind_speed: The wind speed in miles per hour
	:type wind_speed: int | long | decimal.Decimal

	:return: The THSW index temperature in degrees Fahrenheit to one decimal place
	:rtype: decimal.Decimal
	"""
	T = convert_fahrenheit_to_celsius(temperature)
	RH = _as_decimal(relative_humidity)
	WS = convert_miles_per_hour_to_meters_per_second(_as_decimal(wind_speed))

	E = RH / 100 * THSW_6_105 * (THSW_17_27 * T / (THSW_237_7 + T)).exp()
	Thsw = T + (THSW_0_348 * E) - (THSW_0_70 * WS) + THSW_0_70 * (solar_radiation / (WS + 10)) - THSW_4_25

	return convert_celsius_to_fahrenheit(Thsw).quantize(ONE_TENTH)


def calculate_cooling_degree_days(average_temperature):
	"""
	Calculates the cooling degree days for a given day based on its average temperature. The result of this is only
	valid for a daily average temperature. Any application of this to a weekly, monthly, or yearly average temperature
	will yield incorrect results. It must be calculated daily and summed over weekly, monthly, or yearly periods.

	:param average_temperature: The average daily temperature in degrees Fahrenheit
	:type average_temperature: int | long | decimal.Decimal

	:return: The cooling degree days, or `None` if the average temperature was less than or equal to 65F
	"""
	if average_temperature <= DEGREE_DAYS_THRESHOLD:
		return None
	return average_temperature - DEGREE_DAYS_THRESHOLD


def calculate_heating_degree_days(average_temperature):
	"""
	Calculates the heating degree days for a given day based on its average temperature. The result of this is only
	valid for a daily average temperature. Any application of this to a weekly, monthly, or yearly average temperature
	will yield incorrect results. It must be calculated daily and summed over weekly, monthly, or yearly periods.

	:param average_temperature: The average daily temperature in degrees Fahrenheit
	:type average_temperature: int | long | decimal.Decimal

	:return: The heating degree days, or `None` if the average temperature was greater than or equal to 65F
	"""
	if average_temperature >= DEGREE_DAYS_THRESHOLD:
		return None
	return DEGREE_DAYS_THRESHOLD - average_temperature


def calculate_10_minute_wind_average(records):
	"""
	Calculates the highest 10-minute wind average over the course of a day's wind samples. It is only applicable if
	all the wind samples represent time frames of 10 minutes or less. If the archive interval or sample rate of the
	weather instrument is longer than 10 minutes for any wind sample, this function returns `None`.

	The input record format should be a list of lists, a list of tuples, a tuple of lists, or a tuple of tuples, in
	the following format:

	(
		(wind_speed, wind_direction, timestamp_station, minutes_covered, ),
		(wind_speed, wind_direction, timestamp_station, minutes_covered, ),
		(wind_speed, wind_direction, timestamp_station, minutes_covered, ),
		...,
	)

	The wind speed may be any value that can have arithmetic applied to it (specifically, any value that can be summed
	and divided). The wind direction may be any hashable value at all (string, number, etc.), as it is not used or
	manipulated, other than being grouped along with the other values to be returned properly. The timestamp of the
	station must be a `datetime.datetime` and the minutes covered must be an integer, long, or `decimal.Decimal`, as
	they are used together to determine how to weight each record against other records. Minutes covered must be a
	whole number if it is 1 or more, but it may be less than 1 for rapid sample rates (for example, a 2.5-second sample
	rate would yield a minutes-covered value of 0.04166666666667).

	This returns a tuple of (10mwaS, 10mwaD, 10mwaTs, 10mwaTe), where:
		- 10mwaS is the highest 10-minute wind average speed in the same unit as was input
		- 10mwaD is the statistical mode of all the recorded wind directions during the high 10-minute wind average
			period
		- 10mwaTs is start time of the high 10-minute wind average period: in more technical terms, it is the result
			of the following:
			- If the number of minutes covered is less than or equal to 1, it is the value of the timestamp from the
				first record in the high 10-minute wind average period
			- If the number of minutes covered is greater than 1, it is 1 less than minutes covered subtracted from
				the value of the timestamp from the first record in the high 10-minute wind average period
		- 10mwaTe is the end time of the high 10-minute wind average period

	The logic behind the start timestamp seems complex, but it's the result of the fact that a single record can
	represent multiple minutes of wind samples, and the provided timestamp only represents the end of the sampling
	period. So, if the number of minutes covered is 10, the timestamp is the end of the 10th minute. The values
	returned, therefore, end up being the timestamp for the end of the 1st minute (the start) and the timestamp for
	the end of the 10th minute (the end). If the number of minutes covered is 1, the timestamp is the end of just that
	minute, but 10 records make up the 10-minute period. So the values returned are the timestamp for the end of the
	1st 1-minute period record (the start) and the timestamp for the end of the 10th 1-minute period record (the end).
	In both cases, all the caller must do to determine the true start time (as opposed to the end timestamp for
	the start minute) is to subtract 1 minute from it.

	:param records: The wind sample records in the above described format
	:type records: list | tuple

	:return: A tuple in the above described format
	:rtype: tuple
	"""
	speed_queue = collections.deque(maxlen=10)
	direction_queue = collections.deque(maxlen=10)
	timestamp_queue = collections.deque(maxlen=10)
	current_max = ZERO
	current_direction_list = []
	current_timestamp_list = []

	for (wind_speed, wind_speed_direction, timestamp_station, minutes_covered, ) in records:
		if minutes_covered > 10:
			# We can't calculate this unless all the records cover 10 or fewer minutes
			return None, None, None, None

		wind_speed = _as_decimal(wind_speed)

		# We want each record to be present in the queue the same number of times as minutes it spans
		# So if a record spans 5 minutes, it counts as 5 items in the 10-minute queue
		speed_queue.extend([wind_speed] * minutes_covered)
		direction_queue.extend([wind_speed_direction] * minutes_covered)

		# The timestamp is special, because we need to do some math with it
		if minutes_covered <= 1:
			timestamp_queue.append(timestamp_station)
		else:
			# The timestamp represents the end of the time span
			timestamp_queue.extend(
				[timestamp_station - datetime.timedelta(minutes=i) for i in range(minutes_covered - 1, -1, -1)]
			)

		if len(speed_queue) == 10:
			# This is the rolling average of the last 10 minutes
			average = sum(speed_queue) / 10
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
	calculate_10_minute_wind_average([]) == (None, None, None, None, )
)
assert (
	calculate_10_minute_wind_average(
		[
			(1, 'NW', datetime.datetime(2016, 4, 29, 6, 5), 5, ),
			(1, 'NNW', datetime.datetime(2016, 4, 29, 6, 15), 10, ),
			(2, 'WNW', datetime.datetime(2016, 4, 29, 6, 26), 11, ),
			(1, 'NE', datetime.datetime(2016, 4, 29, 6, 27), 1, ),
		],
	) == (None, None, None, None, )
)
assert (
	calculate_10_minute_wind_average(
		[
			(1, 'NW', datetime.datetime(2016, 4, 29, 6, 10), 10, ),
			(1, 'NNW', datetime.datetime(2016, 4, 29, 6, 20), 10, ),
			(2, 'WNW', datetime.datetime(2016, 4, 29, 6, 30), 10, ),
			(1, 'NE', datetime.datetime(2016, 4, 29, 6, 40), 10, ),
		],
	) ==
	(decimal.Decimal('2'), 'WNW', datetime.datetime(2016, 4, 29, 6, 21), datetime.datetime(2016, 4, 29, 6, 30), )
)
assert (
	calculate_10_minute_wind_average(
		[
			(1, 'NW', datetime.datetime(2016, 4, 29, 6, 5), 5, ),
			(1, 'NNW', datetime.datetime(2016, 4, 29, 6, 10), 5, ),
			(2, 'WNW', datetime.datetime(2016, 4, 29, 6, 15), 5, ),
			(1, 'NE', datetime.datetime(2016, 4, 29, 6, 20), 5, ),
		],
	) ==
	(decimal.Decimal('1.5'), 'NNW', datetime.datetime(2016, 4, 29, 6, 6), datetime.datetime(2016, 4, 29, 6, 15), )
)
assert (
	(
		calculate_10_minute_wind_average(
			[
				(1, 'NW', datetime.datetime(2016, 4, 29, 6, 2), 2, ),
				(1, 'NNW', datetime.datetime(2016, 4, 29, 6, 4), 2, ),
				(2, 'N', datetime.datetime(2016, 4, 29, 6, 6), 2, ),
				(1, 'NE', datetime.datetime(2016, 4, 29, 6, 8), 2, ),
				(3, 'NE', datetime.datetime(2016, 4, 29, 6, 10), 2, ),
				(1, 'N', datetime.datetime(2016, 4, 29, 6, 12), 2, ),
				(2, 'NE', datetime.datetime(2016, 4, 29, 6, 14), 2, ),
				(1, 'NNW', datetime.datetime(2016, 4, 29, 6, 16), 2, ),
				(1, 'NNW', datetime.datetime(2016, 4, 29, 6, 18), 2, ),
				(2, 'NNW', datetime.datetime(2016, 4, 29, 6, 20), 2, ),
			],
		)
	) == (decimal.Decimal('1.8'), 'NE', datetime.datetime(2016, 4, 29, 6, 5), datetime.datetime(2016, 4, 29, 6, 14), )
)


def _append_to_list(l, v):
	if v:
		l.append(v)


def calculate_all_record_values(record):
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

	if wind_speed:
		ws_mpm = wind_speed / 60
		distance = ws_mpm * record['minutes_covered']
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
				_append_to_list(
					a,
					calculate_thsw_index(temperature_outside_high, humidity_outside, solar_radiation, ws),
				)
				_append_to_list(
					a,
					calculate_thsw_index(temperature_outside_high, humidity_outside, solar_radiation, wsh),
				)
			if temperature_outside_low and solar_radiation:
				_append_to_list(
					a,
					calculate_thsw_index(temperature_outside_low, humidity_outside, solar_radiation, ws),
				)
				_append_to_list(
					a,
					calculate_thsw_index(temperature_outside_low, humidity_outside, solar_radiation, wsh),
				)
			if temperature_outside and solar_radiation_high:
				_append_to_list(
					a,
					calculate_thsw_index(temperature_outside, humidity_outside, solar_radiation_high, ws),
				)
				_append_to_list(
					a,
					calculate_thsw_index(temperature_outside, humidity_outside, solar_radiation_high, wsh),
				)
			if temperature_outside_high and solar_radiation_high:
				_append_to_list(
					a,
					calculate_thsw_index(temperature_outside_high, humidity_outside, solar_radiation_high, ws),
				)
				_append_to_list(
					a,
					calculate_thsw_index(temperature_outside_high, humidity_outside, solar_radiation_high, wsh),
				)
			if temperature_outside_low and solar_radiation_high:
				_append_to_list(
					a,
					calculate_thsw_index(temperature_outside_low, humidity_outside, solar_radiation_high, ws),
				)
				_append_to_list(
					a,
					calculate_thsw_index(temperature_outside_low, humidity_outside, solar_radiation_high, wsh),
				)
			if a:
				arguments['thsw_index'] = a[0]
				arguments['thsw_index_low'] = min(a)
				arguments['thsw_index_high'] = max(a)

	return arguments
