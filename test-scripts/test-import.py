import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from weatherlink.importer import Importer


importer = Importer(sys.argv[1])

print 'Reading file %s' % importer.file_name
print 'Year %s' % importer.year
print 'Month %s' % importer.month
print

importer.import_data()

for day, day_index in enumerate(importer.header.day_indexes):
	if day > 0 and day_index.record_count > 0:
		print 'Day %s (%s records, offset %s):' % (day, day_index.record_count, day_index.start_index)
		print '-' * 250

		summary = importer.daily_summaries[day]
		output = ''
		for item in summary.DAILY_SUMMARY_ATTRIBUTE_MAP:
			if item[0][-8:] != '_version':
				output += str(summary[item[0]] or '-') + '  '
		print output
		print '-' * 250

		assert day_index.record_count - 2 == len(importer.daily_records[day])

		for record in importer.daily_records[day]:
			output = str(record.date) + '  (' + str(record.timestamp) + ')  '
			for item in record.RECORD_ATTRIBUTE_MAP_WLK:
				if item[0] != '__special' and item[0][-8:] != '_version':
					output += str(record[item[0]] or '-') + '  '
			output += str(record.rain_amount) + '  ' + str(record.rain_rate) + '  '
			print output

		print
