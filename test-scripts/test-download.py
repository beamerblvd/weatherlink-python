import sys

from weatherlink.downloader import Downloader


header_data = (
	'Model=16\r\n'
	'Records=165\r\n'
	'MaxRecords=10240\r\n'
	'ArchiveInt=5\r\n'
	'ConsoleVer=Dec 11 2012\r\n'
	'VantageTX=0\r\n'
)

downloader = Downloader('hello', 'world')

downloader._process_headers(header_data)

assert downloader.console_version == 'Dec 11 2012'
assert downloader.archive_page_size == 5
assert downloader.max_account_records == 10240
assert downloader.record_count == 165

with open(sys.argv[1]) as file_handle:
	downloader._process_download(file_handle)
