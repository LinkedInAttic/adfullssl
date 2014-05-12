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

from adspygoogle import DfpClient
from adspygoogle.dfp import DfpUtils

# The number of items downloaded from DFP.
FETCH_LIMIT = 500

DFP_VERSION = 'v201308'

sys.path.insert(0, os.path.join('..', '..', '..', '..', '..'))
CLIENT = DfpClient(path=os.path.join('..', '..', '..', '..', '..'))


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
  Run the report job and return the csv dump.

  :param report_job: a report job.
  :return: a csv dump of the downloaded data.
  """
  report_service = CLIENT.GetService('ReportService', version=DFP_VERSION)
  job = report_service.RunReportJob(report_job)[0]

  status = job['reportJobStatus']
  while status != 'COMPLETED' and status != 'FAILED':
    time.sleep(30)
    status = report_service.GetReportJob(job['id'])[0]['reportJobStatus']

  return DfpUtils.DownloadReport(job['id'], 'CSV_DUMP', report_service) if status != 'FAILED' else None


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
    print 'At most, %d creatives will be downloaded.' % (len(creative_ids))

  id_str = ','.join(str(i) for i in creative_ids)

  statements = []
  for offset in range(offset, len(creative_ids), FETCH_LIMIT):
    statements.append({
      'query': 'WHERE %s id IN (%s) LIMIT %d OFFSET %d' % (date_setting, id_str, FETCH_LIMIT, offset),
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
    response = creative_service.GetCreativesByStatement(stmt)[0]
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
  return creative_service.UpdateCreatives(dfp_creatives)
