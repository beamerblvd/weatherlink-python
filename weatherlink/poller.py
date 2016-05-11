"""
This module contains classes for continuously polling a Vantage Pro2 weather station for its LOOP1 or LOOP2 (or both)
record packets.
"""

from __future__ import absolute_import

import abc
import threading

from weatherlink.models import LoopRecord
from weatherlink.serial import (
	ConfigurationSettingMixin,
	SerialCommunicator,
	SerialIPCommunicator,
)


class Poller(ConfigurationSettingMixin, SerialCommunicator):
	__metaclass__ = abc.ABCMeta

	POLL_INSTRUCTION = 'LPS %s %s\n'

	# Set poller.packet_type to one of these (defaults to LOOP2), or set it to
	# PACKET_TYPE_LOOP1 | PACKET_TYPE_LOOP2 to get both types
	PACKET_TYPE_LOOP1 = 1
	PACKET_TYPE_LOOP2 = 2

	def __init__(self, *args, **kwargs):
		super(Poller, self).__init__(*args, **kwargs)

		self.packet_type = LoopRecord.PACKET_TYPE_LOOP2
		self._stop_event = None

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
		self._send_instruction(self.POLL_INSTRUCTION % (self.packet_type, num_packets, ))

	def _receive_loop_packets(self, num_packets, callback=None):
		packets = []

		with self._get_file_handle() as handle:
			for i in range(0, num_packets):
				if self._stop_event and self._stop_event.is_set():
					self._send_data('\r')
					return

				if self.packet_type == self.PACKET_TYPE_LOOP1 | self.PACKET_TYPE_LOOP2:
					packet = LoopRecord.load_loop_1_2_from_connection(handle)
				elif self.packet_type == self.PACKET_TYPE_LOOP1:
					packet = LoopRecord.load_loop_1_from_connection(handle)
				else:
					packet = LoopRecord.load_loop_2_from_connection(handle)

				if callback:
					callback(packet)
				else:
					packets.append(packet)

		if not callback:
			return packets


class IPPoller(SerialIPCommunicator, Poller):
	def __init__(self, host, port=SerialIPCommunicator.DEFAULT_PORT_NUMBER):
		super(IPPoller, self).__init__(host, port)
