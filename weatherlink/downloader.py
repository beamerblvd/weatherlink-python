from __future__ import absolute_import

import requests

from weatherlink.models import (
	InstantaneousRecord,
	convert_datetime_to_timestamp,
)


_requests_session = requests.Session()


class Downloader(object):
	WEATHER_LINK_URL = 'http://weatherlink.com/webdl.php?timestamp={timestamp}&user={username}&pass={password}&action={action}'
	ACTION_HEADERS = 'headers'
	ACTION_DOWNLOAD = 'data'
	ARCHIVE_RECORD_LENGTH = 52

	def __init__(self, username, password):
		assert username
		assert password

		self.username = username
		self.password = password

		self.console_version = None
		self.archive_page_size = None
		self.record_count = None
		self.max_account_records = None
		self.records = None

	def download(self, from_timestamp):
		timestamp = convert_datetime_to_timestamp(from_timestamp)

		url = self.WEATHER_LINK_URL.format(
			timestamp=timestamp,
			username=self.username,
			password=self.password,
			action=self.ACTION_HEADERS,
		)

		response = _requests_session.get(url)
		assert response.headers['Content-Type'] == 'text/html', '%s' % response.headers['Content-Type']

		self._process_headers(response.text)

		url = self.WEATHER_LINK_URL.format(
			timestamp=timestamp,
			username=self.username,
			password=self.password,
			action=self.ACTION_DOWNLOAD,
		)

		response = _requests_session.get(url, stream=True)
		assert response.headers['Content-Type'] == 'application/octet-stream', '%s' % response.headers['Content-Type']
		assert response.headers['Content-Transfer-Encoding'] == 'binary', '%s' % response.headers['Content-Transfer-Encoding']

		self._process_download(response.raw)

	def _process_headers(self, header_response_text):
		header_lines = header_response_text.splitlines()
		headers = {}
		for line in header_lines:
			k, v = line.split('=', 1)
			headers[k.strip()] = v.strip()

		assert headers['Model'] == '16'

		self.console_version = headers['ConsoleVer']
		self.archive_page_size = int(headers['ArchiveInt'])
		self.record_count = int(headers['Records'])
		self.max_account_records = int(headers['MaxRecords'])

	def _process_download(self, download_response_handle):
		self.records = []

		for i in range(0, self.record_count):
			record = InstantaneousRecord.load_from_download(download_response_handle)
			if not record:
				break

			self.records.append(record)
