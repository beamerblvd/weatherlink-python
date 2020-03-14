from __future__ import absolute_import

import requests

from weatherlink.models import (
	ArchiveIntervalRecord,
	convert_datetime_to_timestamp,
)


_requests_session = requests.Session()


class Downloader(object):
	WEATHER_LINK_URL = (
		'https://api.weatherlink.com/webdl.php?'
		'timestamp={timestamp}&user={username}&pass={password}&apiToken={api_token}&action={action}'
	)
	ACTION_HEADERS = 'headers'
	ACTION_DOWNLOAD = 'data'
	ARCHIVE_RECORD_LENGTH = 52

	def __init__(self, username, password, api_token):
		if not (username and password and api_token):
			raise ValueError('Username, password, and API token are required')

		self.username = username
		self.password = password
		self.api_token = api_token

		self.console_version = None
		self.record_minute_span = None
		self.record_count = None
		self.max_account_records = None
		self.records = None

	def download(self, from_timestamp):
		timestamp = convert_datetime_to_timestamp(from_timestamp)

		url = self.WEATHER_LINK_URL.format(
			timestamp=timestamp,
			username=self.username,
			password=self.password,
			api_token=self.api_token,
			action=self.ACTION_HEADERS,
		)

		response = _requests_session.get(url)
		if response.headers['Content-Type'] not in ('text/html', 'text/plain'):
			raise AssertionError(str(response.headers['Content-Type']))

		self._process_headers(response.text)

		url = self.WEATHER_LINK_URL.format(
			timestamp=timestamp,
			username=self.username,
			password=self.password,
			api_token=self.api_token,
			action=self.ACTION_DOWNLOAD,
		)

		headers = {'Accept-Encoding': 'identity'}

		response = _requests_session.get(url, headers=headers, stream=True)
		if response.headers['Content-Type'] != 'application/octet-stream':
			raise AssertionError(str(response.headers['Content-Type']))
		if response.headers['Content-Transfer-Encoding'] != 'binary':
			raise AssertionError(str(response.headers['Content-Transfer-Encoding']))

		if response.headers.get('Content-Encoding') in ('br', 'compress', 'deflate', 'gzip'):
			raise ValueError('Got response with unacceptable content encoding %s' % response.headers['Content-Encoding'])

		self._process_download(response.raw)

	def _process_headers(self, header_response_text):
		header_lines = header_response_text.splitlines()
		headers = {}
		for line in header_lines:
			k, v = line.split('=', 1)
			headers[k.strip()] = v.strip()

		if headers['Model'] != '16':
			raise AssertionError(headers['Model'])

		self.console_version = headers['ConsoleVer']  # The console firmware version
		self.record_minute_span = int(headers['ArchiveInt'])  # The console "archive interval" in minutes
		self.record_count = int(headers['Records'])  # The number of records included in this response
		self.max_account_records = int(headers['MaxRecords'])  # The maximum records this account will store

		# For future possible use, the maximum time frame stored on the servers is the archive interval
		# in minutes multiplied by the maximum records this account will store.

	def _process_download(self, download_response_handle):
		self.records = []

		for i in range(0, self.record_count):
			try:
				record = ArchiveIntervalRecord.load_from_download(download_response_handle, self.record_minute_span)
				if not record:
					print('WARN: Halted at record %s because false-y' % i)
					break

				self.records.append(record)
			except AssertionError:
				continue
