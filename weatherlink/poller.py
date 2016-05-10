from __future__ import absolute_import

import curses.ascii
import socket
import threading

from weatherlink.models import LoopRecord


class Poller(object):
	DEFAULT_PORT_NUMBER = 22222

	ACK_BYTE = chr(curses.ascii.ACK)

	POLL_INSTRUCTION = 'LPS %s %s\n'

	# Set poller.packet_type to one of these (defaults to LOOP2), or set it to
	# PACKET_TYPE_LOOP1 | PACKET_TYPE_LOOP2 to get both types
	PACKET_TYPE_LOOP1 = 1
	PACKET_TYPE_LOOP2 = 2

	def __init__(self, host, port=DEFAULT_PORT_NUMBER):
		self.host = host
		self.port = port

		self.packet_type = LoopRecord.PACKET_TYPE_LOOP2

		self._socket = None
		self._stop_event = None

	def connect(self):
		if self._socket:
			raise ValueError('Cannot connect when already connected.')

		try:
			self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self._socket.connect((self.host, self.port, ))
		except:
			if self._socket:
				try:
					self.disconnect()
				except IOError:
					pass
			raise

	def disconnect(self):
		if not self._socket:
			raise ValueError('Cannot disconnect when not connected.')

		try:
			self._socket.close()
		finally:
			self._socket = None

	def __enter__(self):
		self.connect()

	def __exit__(self, exception_type, exception_value, exception_traceback):
		try:
			self.disconnect()
		except:
			# Only allow this exception to be raised if an exception did not trigger the context manager exit
			if not exception_type:
				raise

	def poll(self, num_packets):
		self._send_poll_instruction(num_packets)

		return self._receive_loop_packets(num_packets)

	def start_background_polling(self, num_packets, callback):
		if self._stop_event:
			raise ValueError('Cannot start background polling when already running.')

		self._stop_event = threading.Event()

		self._send_poll_instruction(num_packets)

		thread = threading.Thread(target=self._receive_loop_packets, args=(num_packets, callback, ))
		thread.start()

	def stop_background_polling(self):
		if not self._stop_event:
			raise ValueError('Cannot stop background polling when not running.')

		self._stop_event.set()

	def _send_poll_instruction(self, num_packets):
		self._socket.sendall(self.POLL_INSTRUCTION % (self.packet_type, num_packets, ))

		ack = self._socket.recv(1)
		if ack != self.ACK_BYTE:
			raise IOError('Expected ACK response 0x06, received %s instead.' % ack)

	def _receive_loop_packets(self, num_packets, callback=None):
		packets = []

		with self._socket.makefile() as socket_file:
			for i in range(0, num_packets):
				if self._stop_event and self._stop_event.is_set():
					self._socket.sendall('\r')
					return

				if self.packet_type == self.PACKET_TYPE_LOOP1 | self.PACKET_TYPE_LOOP2:
					packet = LoopRecord.load_loop_1_2_from_connection(socket_file)
				elif self.packet_type == self.PACKET_TYPE_LOOP1:
					packet = LoopRecord.load_loop_1_from_connection(socket_file)
				else:
					packet = LoopRecord.load_loop_2_from_connection(socket_file)

				if callback:
					callback(packet)
				else:
					packets.append(packet)

		if not callback:
			return packets
