from __future__ import absolute_import

import collections

from weatherlink.models import (
	Header,
	DailySummary,
	ArchiveIntervalRecord,
)


class Importer(object):
	FILE_EXTENSION = '.wlk'
	FILE_EXTENSION_LENGTH = len(FILE_EXTENSION)
	EXPECTED_FILE_NAME_LENGTH = 7

	def __init__(self, file_name):
		if not file_name:
			raise ValueError('file_name')
		if file_name[-self.FILE_EXTENSION_LENGTH:] != self.FILE_EXTENSION:
			raise ValueError('file_name')

		self.file_name = file_name

		start_index = -(self.FILE_EXTENSION_LENGTH + self.EXPECTED_FILE_NAME_LENGTH)
		year, month = file_name[start_index:][:self.EXPECTED_FILE_NAME_LENGTH].split('-')

		self.year = int(year)
		self.month = int(month)

		self.header = None
		self.daily_summaries = None
		self.records = None
		self.daily_records = None

	def import_data(self):
		with open(self.file_name, 'rb') as file_handle:
			self.header = Header.load_from_wlk(file_handle)
			self.daily_summaries = {}
			self.records = []
			self.daily_records = collections.defaultdict(list)

			for day, day_index in enumerate(self.header.day_indexes):
				if day > 0:
					for r in range(0, day_index.record_count - 1):
						if r == 0:
							self.daily_summaries[day] = DailySummary.load_from_wlk(
								file_handle,
								self.year,
								self.month,
								day,
							)
						else:
							record = ArchiveIntervalRecord.load_from_wlk(file_handle, self.year, self.month, day)
							self.records.append(record)
							self.daily_records[day].append(record)
