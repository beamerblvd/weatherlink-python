import struct
import pprint

import requests

from weatherlink.models import (
	InstantaneousRecord,
	convert_timestamp_to_datetime,
)


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

	def download(self, from_datetime):
		pass

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
		for i in range(0, self.record_count):
			record = InstantaneousRecord.load_from_download(download_response_handle)
			if not record:
				break

			pprint.pprint(record)
		# while True:
		#     raw_record = download_response_handle.read(self.ARCHIVE_RECORD_LENGTH)
		#     if not raw_record:
		#         break

		#     date_time_stamps = struct.unpack_from('=hh', raw_record)
		#     if date_time_stamps[0] < 1:
		#         continue

		#     print convert_timestamp_to_datetime((date_time_stamps[0] << 16) + date_time_stamps[1])
