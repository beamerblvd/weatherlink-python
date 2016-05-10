import curses.ascii
import datetime
import socket
import struct

from weatherlink.models import (
	calculate_weatherlink_crc,
	RainCollectorTypeSerial,
)


with open('tests/scripts/test-loop-output.bin', 'wb') as handle:
	epoch = datetime.datetime.utcfromtimestamp(0)
	timestamp = int((datetime.datetime.utcnow() - epoch).total_seconds())

	handle.write(struct.pack('<L', timestamp))

	handle.write('\n')

	print 'Connecting to WeatherLinkIP...'
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.connect(('192.168.1.132', 22222, ))
	print

	print 'Reading rain collector size...'
	sock.sendall('EEBRD 2B 01\n')  # "read the EEPROM," "start at position x2B / 43 (setup bits)," "read 0x01 / 1 bytes"
	ack = sock.recv(1)
	if ack == chr(curses.ascii.ACK):
		print 'Expected ACK received...'
	else:
		print 'Unknown ACK received: %s...' % ack
	setup_bits = sock.recv(1)
	crc = sock.recv(2)
	print 'CRC: %s vs %s = result %s...' % (
		calculate_weatherlink_crc(setup_bits),
		struct.unpack_from('<h', crc)[0],
		calculate_weatherlink_crc(setup_bits + crc),
	)
	collector_type = RainCollectorTypeSerial(setup_bits & 0x30)
	print 'Rain collector type is %s.' % collector_type
	print

	print 'Requesting loop packets...'
	sock.sendall('LPS 2 30\n')  # "request loop packets," "type LOOP2," "30 packets"

	ack = sock.recv(1)
	if ack == chr(curses.ascii.ACK):
		print 'Expected ACK received...'
	else:
		print 'Unknown ACK received: %s...' % ack
	handle.write(struct.pack('<B', ord(ack)))

	sock_file = sock.makefile()
	for i in range(0, 15):
		data = sock_file.read(99)
		handle.write(data)
		handle.flush()

		(
			bar_trend, barometer, in_temp, in_hum, out_temp, wind, wind_direction, w10ma, w2ma, w10mg, w10mgd, dew,
			out_hum, heat, chill, thsw, rain, uv, rad, r_storm, r_day, r_15, r_60, evap, r_24, minute,
		) = struct.unpack_from('<3xb3xHHBHBxHHHHH4xhxBxhhhHBHH2xHHHHH19xB19x', data)

		barometer = float(barometer) / 1000
		in_temp = float(in_temp) / 10
		out_temp = float(out_temp) / 10
		w10ma = float(w10ma) / 10
		w2ma = float(w2ma) / 10
		w10mg = float(w10mg) / 10

		print '%s: %s' % (
			(i + 1),
			(
				bar_trend, barometer, in_temp, in_hum, out_temp, wind, wind_direction, w10ma, w2ma, w10mg, w10mgd, dew,
				out_hum, heat, chill, thsw, rain, uv, rad, r_storm, r_day, r_15, r_60, evap, r_24, minute,
			),
		)

		print 'CRC: %s vs %s = result %s' % (
			calculate_weatherlink_crc(data[:-2]),
			struct.unpack_from('<h', data[-2:])[0],
			calculate_weatherlink_crc(data),
		)

sock.close()
