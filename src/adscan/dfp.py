# Copyright 2014 LinkedIn Corp. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.

"""
Utility functions for handling DoubleClick for Publishers (DFP) API.

For more information about DFP API, please refer to https://developers.google.com/doubleclick-publishers/.

Requires Google Ads APIs Python Client Libraries - https://github.com/googleads/googleads-python-legacy-lib.
"""

import os
import sys
import time
import datetime
import tempfile
import gzip

import googleads.dfp
import googleads.errors


DFP_VERSION = 'v201505'

CLIENT = googleads.dfp.DfpClient.LoadFromStorage()


def create_report_service_job(days_ago=2, country=None):
  """
  Create a job for a DFP report service to fetch creative ids.

  :param days_ago: a number that represents days the creatives are served.
  :param country: a comma-delimited country names. If this option is set, the creative only served in
    this countries are downloaded.
  :return: a job for DFP report service.
  """
  days = datetime.date.today() - datetime.timedelta(days=days_ago)
  date_obj = {
    'year': str(days.year),
    'month': str(days.month),
    'day': str(days.day)
  }
  report_job = {
    'reportQuery': {
      'dimensions': ['CREATIVE_ID'],
      'statement': '',
      'columns': ['AD_SERVER_IMPRESSIONS'],
      'dateRangeType': 'CUSTOM_DATE',
      'startDate': date_obj,
      'endDate': date_obj
    }
  }

  if country:
    countries = country.split(',')
    report_job['reportQuery']['statement'] = {'query': 'WHERE COUNTRY_NAME IN (\'%s\')' % '\',\''.join(countries)}

  return report_job


def run_report_service_job(report_job):
  """
  Run the report job and return a list of creative ids.

  :param report_job: a report job.
  :return: a list of creative ids.
  """
  data_downloader = CLIENT.GetDataDownloader(version=DFP_VERSION)
  try:
    report_job_id = data_downloader.WaitForReport(report_job)
  except googleads.errors.DfpReportError, e:
    print 'Failed to generate report. [Error] %s' % e
    raise e
  report_file = tempfile.NamedTemporaryFile(suffix='.csv.gz', delete=False)
  data_downloader.DownloadReportToFile(report_job_id, 'CSV_DUMP', report_file)
  report_file.close()

  report = gzip.open(report_file.name)
  ids = [r.split(',')[0] for r in report]
  report.close()

  os.remove(report_file.name)
  # Ignore the first line, which contains this line "Dimension.CREATIVE_ID,Column.AD_SERVER_IMPRESSIONS"
  return ids[1:]


def create_creative_service_statement(creative_ids, offset=0, only_new=True, days_ago=2):
  """
  Download creatives from DFP.

  :param creative_ids: a list of creative ids.
  :param offset: the offset for the list to start download from.
  :param only_new: a boolean that indicates whether downloading only recently updated creatives or not.
  :param days_ago: a number that represents days the creatives are served.
  :return: a list of creatives.
  """
  values = []
  date_setting = ''

  if only_new:
    date_setting = 'lastModifiedDateTime > :date AND'
    days = datetime.date.today() - datetime.timedelta(days=days_ago)
    values.append({
      'key': 'date',
      'value': {
        'xsi_type': 'TextValue',
        'value': days.strftime('%Y-%m-%dT%H:%M:%S')
      }
    })
    print 'Only recently updated creatives will be downloaded.'
  else:
    print 'At most, %d creatives will be downloaded.' % len(creative_ids)

  id_str = ','.join(str(i) for i in creative_ids)

  statements = []
  for offset in range(offset, len(creative_ids), googleads.dfp.SUGGESTED_PAGE_LIMIT):
    statements.append({
      'query': 'WHERE %s id IN (%s) LIMIT %d OFFSET %d' % (date_setting, id_str, googleads.dfp.SUGGESTED_PAGE_LIMIT, offset),
      'values': values
    })
  return statements


def run_creative_service_statements(statements):
  """
  Download creatives from DFP.

  :param statements: a list of CreativeService statements to download creatives.
  :return: a list of creatives.
  """
  print '%d statements will be executed on DFP Creative Service' % len(statements)

  creative_service = CLIENT.GetService('CreativeService', version=DFP_VERSION)

  creatives = []
  for stmt in statements:
    response = creative_service.getCreativesByStatement(stmt)
    results = response['results'] if 'results' in response else []

    print 'Fetched data size: %d.' % len(results)

    if len(results) > 0:
      creatives.extend(results)
    else:
      break
  return creatives


def upload_creatives(dfp_creatives):
  """
  Upload the creatives to DFP.

  :param dfp_creatives: a list of DFP creatives.
  :return: a list of updated creatives.
  """
  creative_service = CLIENT.GetService('CreativeService', version=DFP_VERSION)
  return creative_service.updateCreatives(dfp_creatives)
