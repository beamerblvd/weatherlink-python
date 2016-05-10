import curses.ascii
import datetime
import os
import socket
import struct
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))

from weatherlink.models import calculate_weatherlink_crc

# with open('test-loop-output.bin', 'wb') as handle:
# 	epoch = datetime.datetime.utcfromtimestamp(0)
# 	timestamp = int((datetime.datetime.utcnow() - epoch).total_seconds())
#
# 	handle.write(struct.pack('<L', timestamp))
#
# 	handle.write('\n')
#
# 	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# 	sock.connect(('192.168.1.132', 22222, ))
# 	sock.sendall('LPS 2 15\n')
#
# 	ack = sock.recv(1)
# 	if ack == chr(curses.ascii.ACK):
# 		print 'Expected ACK received.'
# 	else:
# 		print 'Unknown ACK received: %s.' % ack
# 	handle.write(struct.pack('<B', ord(ack)))
#
# 	i = 0
# 	data = sock.recv(99)
# 	while data:
# 		while len(data) < 99:
# 			data += sock.recv(99 - len(data))
# 		handle.write(data)
# 		handle.flush()
#
# 		intro, bar_trend, packet, fill, barometer, in_temp, in_hum, out_temp, wind = struct.unpack('<3sbB2sHHBHB84x', data)
#
# 		barometer = float(barometer) / 1000
# 		in_temp = float(in_temp) / 10
# 		out_temp = float(out_temp) / 10
#
# 		i += 1
# 		print '%s: %s' % (i, (intro, bar_trend, packet, fill, barometer, in_temp, in_hum, out_temp, wind, ), )
# 		if i == 15:
# 			break
# 		data = sock.recv(99)
#
# sock.close()
#

with open('test-loop-output.bin', 'rb') as handle:
	timestamp_read, sep, ack = struct.unpack_from('<L1sB', handle.read(6))
	print 'Timestamp was: %s' % timestamp_read

	if sep == '\n':
		print 'SEP matches'
	else:
		print 'SEP does not match: %s' % sep

	if ack == curses.ascii.ACK:
		print 'ACK matches'
	else:
		print 'ACK does not match: %s' % ack

	for i in range(0, 15):
		data = handle.read(99)
		intro, bar_trend, packet, fill, barometer, in_temp, in_hum, out_temp, wind = struct.unpack_from(
			'<3sbB2sHHBHB84x', data
		)
		barometer = float(barometer) / 1000
		in_temp = float(in_temp) / 10
		out_temp = float(out_temp) / 10

		print '%s: %s' % ((i + 1), (intro, bar_trend, packet, fill, barometer, in_temp, in_hum, out_temp, wind, ), )

		print 'CRC: %s vs %s = result %s' % (
			calculate_weatherlink_crc(data[:-2]),
			struct.unpack_from('<h', data[-2:])[0],
			calculate_weatherlink_crc(data),
		)

# sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# sock.connect(('192.168.1.132', 22222, ))
# sock.sendall('LPS 2 15\n')
#
# ack = sock.recv(1)
# if ack == chr(curses.ascii.ACK):
# 	print 'Expected ACK received.'
# else:
# 	print 'Unknown ACK received: %s.' % ack
#
# socket_file = sock.makefile()
#
# for i in range(0, 15):
# 	intro, bar_trend, packet, fill, barometer, in_temp, in_hum, out_temp, wind = struct.unpack_from('<3sbB2sHHBHB84x', socket_file.read(99))
#
# 	barometer = float(barometer) / 1000
# 	in_temp = float(in_temp) / 10
# 	out_temp = float(out_temp) / 10
#
# 	i += 1
# 	print '%s: %s' % (i, (intro, bar_trend, packet, fill, barometer, in_temp, in_hum, out_temp, wind, ), )
#
# socket_file.close()
# sock.close()
