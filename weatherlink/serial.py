"""
This module contains abstract serial communicator classes for communicating directly with Vantage Pro2 weather stations
using the WeatherLink hardware.
"""

from __future__ import absolute_import

import abc
import contextlib
import curses.ascii
import socket
import struct

import six

from weatherlink.models import calculate_weatherlink_crc


if six.binary_type == str:
	# Values returned by binary file reading are plain strings, binary chars are plain strings in Python 2
	def char_to_byte(char):
		return ord(char)
else:
	# Values returned by binary file reading are binary strings (bytes), binary chars are ints in Python 3
	def char_to_byte(char):
		return char


class AcknowledgmentError(IOError):
	pass


class NotAcknowledgedError(AcknowledgmentError):
	NAK_BYTE = 0x21

	@classmethod
	def raise_if_not_acknowledged(cls, ack):
		ack = char_to_byte(ack)
		if ack == curses.ascii.NAK or ack == cls.NAK_BYTE:
			raise cls('Request not acknowledged by weather console')


class InvalidAcknowledgementError(AcknowledgmentError):
	@classmethod
	def raise_if_not_acknowledged(cls, ack):
		if char_to_byte(ack) != curses.ascii.ACK:
			raise cls('Expected ACK response 0x06, received %s instead.' % ack)


class CRCValidationError(IOError):
	pass


@six.add_metaclass(abc.ABCMeta)
class SerialCommunicator(object):
	"""
	This is an abstract serial communicator class that defines the interface for connecting to and communicating with
	Vantage Pro2 weather stations using the serial protocol through any WeatherLink hardware (WeatherLinkIP,
	WeatherLink USB, and WeatherLink Serial should all be supportable).

	This class does not, itself, do any communication, but it does abstract away a few mundane tasks. It handles
	ACK confirmations and the common pattern of confirming ACKs after sending instructions, and it provides a context
	manager interface so that connect and disconnect do not have to be called directly.
	"""
	def __init__(self, *args, **kwargs):
		"""
		Constructs a serial communicator. *args and **kwargs are specified so that we can have a well-behaving
		multiple-inheritance scheme.
		"""
		del args, kwargs  # These are unused and cannot be passed to object#__init__()
		super(SerialCommunicator, self).__init__()

	@abc.abstractmethod
	def connect(self):
		"""
		This method connects to the weather station using the supported hardware and the serial communication protocol.
		Subclasses must implement this method. It returns nothing. It is an error to call this a second time without
		first calling :func:`SerialCommunicator.disconnect`.

		:raises ValueError: If the communicator is already connected
		"""
		raise NotImplementedError()

	@abc.abstractmethod
	def disconnect(self):
		"""
		This method disconnects from the weather station. Subclasses must implement this method. It returns nothing. It
		is an error to call this before calling :func:`SerialCommunicator.connect`, or to call this a second time
		without calling :func:`SerialCommunicator.connect` again first.

		:raises ValueError: If the communicator is already disconnected
		"""
		raise NotImplementedError()

	def __enter__(self):
		self.connect()

	def __exit__(self, exception_type, *_):
		# noinspection PyBroadException
		try:
			self.disconnect()
		except:
			# Only allow this exception to be raised if an exception did not trigger the context manager exit
			if not exception_type:
				raise

	def confirm_ack(self):
		"""
		Reads a single bite from the serial communications channel and confirms that it is a proper ACK byte.
		Returns nothing.

		:raises NotAcknowledgedError: If the byte read is an NAK byte (0x15) or a ! (0x21)
		:raises InvalidAcknowledgementError: If the byte read is not an ACK byte (0x06)
		"""
		ack = self._read_data(1)[0]
		NotAcknowledgedError.raise_if_not_acknowledged(ack)
		InvalidAcknowledgementError.raise_if_not_acknowledged(ack)

	def _send_instruction(self, command, confirm_ack=True):
		"""
		Sends the provided command and optionally (default) confirms an ACK response.

		:param command: The command to send over the serial communications channel
		:type command: str | unicode
		:param confirm_ack: Whether to call :func:`SerialCommunicator.confirm_ack` after sending the instruction
							(defaults to `True`)
		:type confirm_ack: bool

		:raises AcknowledgmentError: If `confirm_ack` is `True` and the byte read is not an ACK byte
		"""
		self._send_data(command)

		if confirm_ack:
			self.confirm_ack()

	@abc.abstractmethod
	def _send_data(self, data):
		"""
		Sends all of the data specified over the serial communications channel. Blocks until all data is sent or
		an error occurs. Subclasses must implement this method. Returns nothing.

		:param data: The data to send
		:type data: str | unicode

		:raises IOError: If the data could not be sent
		"""
		raise NotImplementedError()

	@abc.abstractmethod
	def _read_data(self, length):
		"""
		Receives data up to the length indicated over the serial communications protocol. Depending on the underlying
		protocol (IP, USB, Serial), this method may or may not block until all the data is read (unless `length` is 1).
		Users must take additional steps to continue calling this method until all data is read, or use
		:func:`SerialCommunicator.get_file_handle` to read the data in a blocking manner. Subclasses must implement
		this method.

		:param length: The amount of data to read
		:type length: int

		:return: The data read
		"""
		raise NotImplementedError()

	@abc.abstractmethod
	def _get_file_handle(self):
		"""
		Returns a buffered file-like object that can be passed to routines expecting file-like objects. This object
		will block on reads until all data is read. Subclasses must implement this method.

		:return: A file-like wrapper around the underlying communications protocol
		:rtype: file
		"""
		raise NotImplementedError()


class SerialIPCommunicator(SerialCommunicator):
	DEFAULT_PORT_NUMBER = 22222

	def __init__(self, host, port, *args, **kwargs):
		super(SerialIPCommunicator, self).__init__(*args, **kwargs)

		self.host = host
		self.port = port

		self._socket = None

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

	def _send_data(self, data):
		self._socket.sendall(data)

	def _read_data(self, length):
		return self._socket.recv(1)

	@contextlib.contextmanager
	def _get_file_handle(self):
		handle = None
		exc = None
		try:
			handle = self._socket.makefile()
			yield handle
		except Exception as e:
			exc = e
			raise
		finally:
			if handle:
				# noinspection PyBroadException
				try:
					handle.close()
				except:
					if not exc:
						raise


@six.add_metaclass(abc.ABCMeta)
class ConfigurationSettingMixin(SerialCommunicator):
	CONFIG_READ_INSTRUCTION = 'EEBRD %s %s\n'
	CONFIG_WRITE_INSTRUCTION = 'EEBWR %s %s\n'

	CONFIG_SETTING_SETUP_BITS = ('2B', '01', )

	SETUP_BITS_MASK_RAIN_COLLECTOR = 0b00110000

	def __init__(self, *args, **kwargs):
		super(ConfigurationSettingMixin, self).__init__(*args, **kwargs)

	def read_config_setting(self, setting_address, setting_length, confirm_crc=True, return_crc=False):
		"""
		Reads a configuration setting from the weather console. Returns the raw setting bytes and optionally
		(default `False`) the CRC. Optionally (default `True`) validates the CRC to confirm the data is correct.
		Returns a `str` in Python 2.7 and `bytes` in Python 3.1+.

		:param setting_address: The address at which the desired setting resides (a number in hex string format)
		:type setting_address: str | unicode
		:param setting_length: The length of the desired setting in bytes (a number in hex string format), not including
								the two CRC bytes (that is added automatically)
		:type setting_length: str | unicode
		:param confirm_crc: Whether the CRC should be checked (defaults to `True`)
		:type confirm_crc: bool
		:param return_crc: Whether the CRC should be included in the returned data (defaults to `False`)
		:type return_crc: bool

		:return: The raw setting bytes, optionally including the CRC as the last two bytes
		:rtype: str | bytes
		:raises AcknowledgmentError: If an incorrect ACK is returned
		:raises CRCValidationError: If `confirm_crc` is `True` and the CRC does not match
		"""
		self._send_instruction(self.CONFIG_READ_INSTRUCTION % (setting_address, setting_length, ))

		with self._get_file_handle() as handle:
			setting = handle.read(int('0x%s' % setting_length, 16) + 2)  # must read the CRC

		if confirm_crc and calculate_weatherlink_crc(setting) != 0:
			raise CRCValidationError('CRC for response %s does not resolve to zero.' % repr(setting))

		return setting if return_crc else setting[:-2]

	def write_config_setting(self, setting_address, setting_length, setting_value):
		"""
		Writes a configuration setting to the weather console. The length of the `setting_value` must match the value
		of `setting_length`. Returns nothing. Setting value should be a `str` in Python 3.7 and `bytes` in Python 3.1+.

		:param setting_address: The address at which the desired setting resides (a number in hex string format)
		:type setting_address: str | unicode
		:param setting_length: The length of the desired setting in bytes (a number in hex string format), not including
								the two CRC bytes (that is calculated and added automatically)
		:type setting_length: str | unicode
		:param setting_value: The new setting value, not including the twe CRC bytes (that is calculated and added
								automatically)
		:type setting_value: str | bytes

		:raises ValueError: If the setting value length and setting length do not match
		:raises AcknowledgmentError: If an incorrect ACK is returned
		:raises CRCValidationError: If the calculated CRC, appended to the setting value, does not result in a CRC
									validation value of 0.
		"""
		if len(setting_value) != int('0x%s' % setting_length, 16):
			raise ValueError('The length of the setting value does not match the setting length.')

		self._send_instruction(self.CONFIG_WRITE_INSTRUCTION % (setting_address, setting_length, ))

		crc = calculate_weatherlink_crc(setting_value)
		data = setting_value + struct.pack('>H', crc)  # Unlike other little-endian data, CRCs are big-endian (eye roll)

		verified_crc = calculate_weatherlink_crc(data)
		if verified_crc != 0:
			raise CRCValidationError(
				'CRC %s for data %s did not result in a CRC verification of 0, was %s.' % (
					crc,
					repr(setting_value),
					verified_crc,
				)
			)

		self._send_data(data)

	def read_setup_bit(self, mask):
		"""
		Reads the 8 setup bits (1 byte) from the weather console and masks it with the given mask, returning the
		value of the setting.

		:param mask: The mask to apply to obtain the setting from the setup bits
		:type mask: int

		:return: The value of the setting
		:rtype: int
		:raises AcknowledgmentError: If an incorrect ACK is returned
		:raises CRCValidationError: If the CRC does not match
		"""
		setup_bits = ord(self.read_config_setting(*self.CONFIG_SETTING_SETUP_BITS))
		return setup_bits & mask

	def read_rain_collector_type(self):
		"""
		Reads and returns the rain collector type from the setup bits in the configuration settings.

		:return: The rain collector type integer
		:rtype: int
		:raises AcknowledgmentError: If an incorrect ACK is returned
		:raises CRCValidationError: If the CRC does not match
		"""
		return self.read_setup_bit(self.SETUP_BITS_MASK_RAIN_COLLECTOR)
