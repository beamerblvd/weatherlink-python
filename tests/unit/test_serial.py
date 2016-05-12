from __future__ import absolute_import

import mock
from unittest import TestCase

import six

from weatherlink.models import RainCollectorTypeSerial
from weatherlink.serial import (
	ConfigurationSettingMixin,
	CRCValidationError,
	InvalidAcknowledgementError,
	NotAcknowledgedError,
	SerialCommunicator,
	SerialIPCommunicator,
)


class TestSerialCommunicator(TestCase):
	@mock.patch.multiple('weatherlink.serial.SerialCommunicator', __abstractmethods__=set())
	def setUp(self):
		self.communicator = SerialCommunicator()

	@mock.patch('weatherlink.serial.SerialCommunicator.disconnect')
	@mock.patch('weatherlink.serial.SerialCommunicator.connect')
	def test_instance_context_manager_connect_fails(self, mock_connect, mock_disconnect):
		mock_connect.side_effect = ValueError

		self.assertFalse(mock_connect.called)
		self.assertFalse(mock_disconnect.called)

		context = {'reached': False}

		with self.assertRaises(ValueError):
			with self.communicator:
				context['reached'] = True

		self.assertFalse(context['reached'])
		mock_connect.assert_called_once_with()
		self.assertFalse(mock_disconnect.called)

	@mock.patch('weatherlink.serial.SerialCommunicator.disconnect')
	@mock.patch('weatherlink.serial.SerialCommunicator.connect')
	def test_instance_context_manager_disconnect_fails(self, mock_connect, mock_disconnect):
		mock_disconnect.side_effect = IOError

		self.assertFalse(mock_connect.called)
		self.assertFalse(mock_disconnect.called)

		with self.assertRaises(IOError):
			with self.communicator:
				mock_connect.assert_called_once_with()
				self.assertFalse(mock_disconnect.called)

		mock_connect.assert_called_once_with()
		mock_disconnect.assert_called_once_with()

	@mock.patch('weatherlink.serial.SerialCommunicator.disconnect')
	@mock.patch('weatherlink.serial.SerialCommunicator.connect')
	def test_instance_context_manager_inside_fails(self, mock_connect, mock_disconnect):
		self.assertFalse(mock_connect.called)
		self.assertFalse(mock_disconnect.called)

		with self.assertRaises(ArithmeticError):
			with self.communicator:
				mock_connect.assert_called_once_with()
				self.assertFalse(mock_disconnect.called)
				raise ArithmeticError()

		mock_connect.assert_called_once_with()
		mock_disconnect.assert_called_once_with()

	@mock.patch('weatherlink.serial.SerialCommunicator.disconnect')
	@mock.patch('weatherlink.serial.SerialCommunicator.connect')
	def test_instance_context_manager_inside_and_disconnect_fail(self, mock_connect, mock_disconnect):
		mock_disconnect.side_effect = IOError

		self.assertFalse(mock_connect.called)
		self.assertFalse(mock_disconnect.called)

		with self.assertRaises(ArithmeticError):
			with self.communicator:
				mock_connect.assert_called_once_with()
				self.assertFalse(mock_disconnect.called)
				raise ArithmeticError()

		mock_connect.assert_called_once_with()
		mock_disconnect.assert_called_once_with()

	@mock.patch('weatherlink.serial.SerialCommunicator.disconnect')
	@mock.patch('weatherlink.serial.SerialCommunicator.connect')
	def test_instance_context_manager_succeeds(self, mock_connect, mock_disconnect):
		self.assertFalse(mock_connect.called)
		self.assertFalse(mock_disconnect.called)

		with self.communicator:
			mock_connect.assert_called_once_with()
			self.assertFalse(mock_disconnect.called)

		mock_connect.assert_called_once_with()
		mock_disconnect.assert_called_once_with()

	@mock.patch('weatherlink.serial.SerialCommunicator._read_data')
	def test_confirm_ack_succeeds(self, mock_read_data):
		mock_read_data.return_value = b'\x06'

		self.communicator.confirm_ack()

		mock_read_data.assert_called_once_with(1)

	@mock.patch('weatherlink.serial.SerialCommunicator._read_data')
	def test_confirm_ack_nak1(self, mock_read_data):
		mock_read_data.return_value = b'\x15'

		with self.assertRaises(NotAcknowledgedError):
			self.communicator.confirm_ack()

		mock_read_data.assert_called_once_with(1)

	@mock.patch('weatherlink.serial.SerialCommunicator._read_data')
	def test_confirm_ack_nak2(self, mock_read_data):
		mock_read_data.return_value = b'\x21'

		with self.assertRaises(NotAcknowledgedError):
			self.communicator.confirm_ack()

		mock_read_data.assert_called_once_with(1)

	@mock.patch('weatherlink.serial.SerialCommunicator._read_data')
	def test_confirm_ack_fails(self, mock_read_data):
		mock_read_data.return_value = b'\x04'

		with self.assertRaises(InvalidAcknowledgementError):
			self.communicator.confirm_ack()

		mock_read_data.assert_called_once_with(1)

	@mock.patch('weatherlink.serial.SerialCommunicator.confirm_ack')
	@mock.patch('weatherlink.serial.SerialCommunicator._send_data')
	def test_send_instruction(self, mock_send_data, mock_confirm_ack):
		self.communicator._send_instruction('FOOBAR 01 70\n')

		mock_send_data.assert_called_once_with('FOOBAR 01 70\n')
		mock_confirm_ack.assert_called_once_with()

		mock_send_data.reset_mock()
		mock_confirm_ack.reset_mock()

		self.communicator._send_instruction('BAZ 05 48\n', False)

		mock_send_data.assert_called_once_with('BAZ 05 48\n')
		self.assertFalse(mock_confirm_ack.called)

		mock_send_data.reset_mock()
		mock_confirm_ack.reset_mock()

		self.communicator._send_instruction('QUX 2B 01\n', True)

		mock_send_data.assert_called_once_with('QUX 2B 01\n')
		mock_confirm_ack.assert_called_once_with()


class TestSerialIPCommunicator(TestCase):
	def setUp(self):
		self.communicator = SerialIPCommunicator('127.0.0.1', 0)  # TODO


class TestConfigurationSettingMixin(TestCase):
	@mock.patch.multiple('weatherlink.serial.ConfigurationSettingMixin', __abstractmethods__=set())
	def setUp(self):
		self.communicator = ConfigurationSettingMixin()

	@mock.patch('weatherlink.serial.calculate_weatherlink_crc')
	@mock.patch('weatherlink.serial.ConfigurationSettingMixin._get_file_handle')
	@mock.patch('weatherlink.serial.ConfigurationSettingMixin._send_instruction')
	def test_read_config_setting_defaults(self, mock_send_instruction, mock_get_file_handle, mock_crc):
		mock_get_file_handle.return_value = mock.MagicMock(spec=file)
		mock_get_file_handle.return_value.__enter__.return_value.read.return_value = b'\xFF\xE3\x03\x41'
		mock_crc.return_value = 0

		setting = self.communicator.read_config_setting('3C', '02')

		self.assertEqual(b'\xFF\xE3', setting)

		mock_send_instruction.assert_called_once_with('EEBRD 3C 02\n')
		mock_get_file_handle.assert_called_once_with()
		mock_get_file_handle.return_value.__enter__.assert_called_once()
		mock_get_file_handle.return_value.__exit__.assert_called_once()
		mock_get_file_handle.return_value.__enter__.return_value.read.assert_called_once_with(4)
		mock_crc.assert_called_once_with(b'\xFF\xE3\x03\x41')

	@mock.patch('weatherlink.serial.calculate_weatherlink_crc')
	@mock.patch('weatherlink.serial.ConfigurationSettingMixin._get_file_handle')
	@mock.patch('weatherlink.serial.ConfigurationSettingMixin._send_instruction')
	def test_read_config_setting_return_crc(self, mock_send_instruction, mock_get_file_handle, mock_crc):
		mock_get_file_handle.return_value = mock.MagicMock(spec=file)
		mock_get_file_handle.return_value.__enter__.return_value.read.return_value = b'\xF3\x14\x5E'
		mock_crc.return_value = 0

		setting = self.communicator.read_config_setting('2F', '01', return_crc=True)

		self.assertEqual(b'\xF3\x14\x5E', setting)

		mock_send_instruction.assert_called_once_with('EEBRD 2F 01\n')
		mock_get_file_handle.assert_called_once_with()
		mock_get_file_handle.return_value.__enter__.assert_called_once()
		mock_get_file_handle.return_value.__exit__.assert_called_once()
		mock_get_file_handle.return_value.__enter__.return_value.read.assert_called_once_with(3)
		mock_crc.assert_called_once_with(b'\xF3\x14\x5E')

	@mock.patch('weatherlink.serial.calculate_weatherlink_crc')
	@mock.patch('weatherlink.serial.ConfigurationSettingMixin._get_file_handle')
	@mock.patch('weatherlink.serial.ConfigurationSettingMixin._send_instruction')
	def test_read_config_setting_crc_fails(self, mock_send_instruction, mock_get_file_handle, mock_crc):
		mock_get_file_handle.return_value = mock.MagicMock(spec=file)
		mock_get_file_handle.return_value.__enter__.return_value.read.return_value = b'\xFF\xE3\x03\x41'
		mock_crc.return_value = 123489

		with self.assertRaises(CRCValidationError):
			self.communicator.read_config_setting('3C', '02')

		mock_send_instruction.assert_called_once_with('EEBRD 3C 02\n')
		mock_get_file_handle.assert_called_once_with()
		mock_get_file_handle.return_value.__enter__.assert_called_once()
		mock_get_file_handle.return_value.__exit__.assert_called_once()
		mock_get_file_handle.return_value.__enter__.return_value.read.assert_called_once_with(4)
		mock_crc.assert_called_once_with(b'\xFF\xE3\x03\x41')

	@mock.patch('weatherlink.serial.calculate_weatherlink_crc')
	@mock.patch('weatherlink.serial.ConfigurationSettingMixin._get_file_handle')
	@mock.patch('weatherlink.serial.ConfigurationSettingMixin._send_instruction')
	def test_read_config_setting_crc_ignored(self, mock_send_instruction, mock_get_file_handle, mock_crc):
		mock_get_file_handle.return_value = mock.MagicMock(spec=file)
		mock_get_file_handle.return_value.__enter__.return_value.read.return_value = b'\xF3\x14\x5E'
		mock_crc.return_value = 123489

		setting = self.communicator.read_config_setting('2F', '01', confirm_crc=False)

		self.assertEqual(b'\xF3', setting)

		mock_send_instruction.assert_called_once_with('EEBRD 2F 01\n')
		mock_get_file_handle.assert_called_once_with()
		mock_get_file_handle.return_value.__enter__.assert_called_once()
		mock_get_file_handle.return_value.__exit__.assert_called_once()
		mock_get_file_handle.return_value.__enter__.return_value.read.assert_called_once_with(3)
		self.assertFalse(mock_crc.called)

	@mock.patch('weatherlink.serial.ConfigurationSettingMixin.read_config_setting')
	def test_read_setup_bit(self, mock_read_config_setting):
		mock_read_config_setting.return_value = six.int2byte(0b10101110)

		bit = self.communicator.read_setup_bit(0b10)

		self.assertEqual(0b10, bit)
		mock_read_config_setting.assert_called_once_with('2B', '01')

		mock_read_config_setting.reset_mock()

		mock_read_config_setting.return_value = six.int2byte(0b10101101)

		bit = self.communicator.read_setup_bit(0b10)

		self.assertEqual(0b00, bit)
		mock_read_config_setting.assert_called_once_with('2B', '01')

		mock_read_config_setting.reset_mock()

		mock_read_config_setting.return_value = six.int2byte(0b10101101)

		bit = self.communicator.read_setup_bit(0b110)

		self.assertEqual(0b100, bit)
		mock_read_config_setting.assert_called_once_with('2B', '01')

		mock_read_config_setting.reset_mock()

		mock_read_config_setting.return_value = six.int2byte(0b10101111)

		bit = self.communicator.read_setup_bit(0b110)

		self.assertEqual(0b110, bit)
		mock_read_config_setting.assert_called_once_with('2B', '01')

	@mock.patch('weatherlink.serial.ConfigurationSettingMixin.read_config_setting')
	def test_read_rain_collector_type(self, mock_read_config_setting):
		mock_read_config_setting.return_value = six.int2byte(0b10101110)

		collector_type = RainCollectorTypeSerial(self.communicator.read_rain_collector_type())

		self.assertEqual(RainCollectorTypeSerial.millimeters_0_1, collector_type)
		mock_read_config_setting.assert_called_once_with('2B', '01')

		mock_read_config_setting.reset_mock()

		mock_read_config_setting.return_value = six.int2byte(0b10011110)

		collector_type = RainCollectorTypeSerial(self.communicator.read_rain_collector_type())

		self.assertEqual(RainCollectorTypeSerial.millimeters_0_2, collector_type)
		mock_read_config_setting.assert_called_once_with('2B', '01')

		mock_read_config_setting.reset_mock()

		mock_read_config_setting.return_value = six.int2byte(0b10001110)

		collector_type = RainCollectorTypeSerial(self.communicator.read_rain_collector_type())

		self.assertEqual(RainCollectorTypeSerial.inches_0_01, collector_type)
		mock_read_config_setting.assert_called_once_with('2B', '01')
