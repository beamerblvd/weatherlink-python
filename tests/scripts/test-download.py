from __future__ import absolute_import

import dateutil.parser
import sys

from weatherlink.downloader import Downloader
from weatherlink.utils import calculate_all_record_values


# This sample header data can be used to test _process_headers directly
# header_data = (
# 	'Model=16\r\n'
# 	'Records=165\r\n'
# 	'MaxRecords=10240\r\n'
# 	'ArchiveInt=5\r\n'
# 	'ConsoleVer=Dec 11 2012\r\n'
# 	'VantageTX=0\r\n'
# )

# tests/data/sample_download.bin can be used to test _process_download directly

downloader = Downloader(sys.argv[1], sys.argv[2])

downloader.download(dateutil.parser.parse(sys.argv[3]))

print 'Console version: %s' % downloader.console_version
print 'Record minute span: %s' % downloader.record_minute_span
print 'Max records: %s' % downloader.max_account_records
print 'Record count %s' % downloader.record_count
print 'Records processed: %s' % len(downloader.records)

for record in downloader.records:
	output = str(record.date) + '  (' + str(record.timestamp) + ')  '
	for item in record.RECORD_ATTRIBUTE_MAP_DOWNLOAD:
		if item[0] != '__special' and item[0][-8:] != '_version':
			output += str(record[item[0]] or '-') + '  '
	output += str(record.rain_amount) + '  ' + str(record.rain_rate) + '  '
	values = calculate_all_record_values(record)
	output += '(plus %s calculated values)' % len(values)
	print output
