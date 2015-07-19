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

import datetime
import unittest

import adscan.dfp
import googleads.dfp


class DfpTestCase(unittest.TestCase):
  """
  Test the dfp module.
  """

  @classmethod
  def create_report_service_job(cls, days_ago=2, country=None):
    """
    Test the create_report_service_job method.
    """
    report_job = adscan.dfp.create_report_service_job(days_ago=days_ago, country=country)

    days = datetime.date.today() - datetime.timedelta(days=days_ago)

    assert report_job['reportQuery']['dimensions'] == ['CREATIVE_ID']
    if country:
      countries = country.split(',')
      assert report_job['reportQuery']['statement']['query'] == ('WHERE COUNTRY_NAME IN (\'%s\')' % '\',\''.join(countries))
    else:
      assert report_job['reportQuery']['statement'] == ''
    assert report_job['reportQuery']['columns'] == ['AD_SERVER_IMPRESSIONS']
    assert report_job['reportQuery']['dateRangeType'] == 'CUSTOM_DATE'
    assert report_job['reportQuery']['startDate']['year'] == str(days.year)
    assert report_job['reportQuery']['startDate']['month'] == str(days.month)
    assert report_job['reportQuery']['startDate']['day'] == str(days.day)
    assert report_job['reportQuery']['endDate']['year'] == str(days.year)
    assert report_job['reportQuery']['endDate']['month'] == str(days.month)
    assert report_job['reportQuery']['endDate']['day'] == str(days.day)

  @classmethod
  def create_creative_service_statement(cls, creative_ids, offset=0, only_new=True, days_ago=2):
    """
    Test the create_creative_service_statement method.
    """
    statements = adscan.dfp.create_creative_service_statement(creative_ids, offset=offset, only_new=only_new, days_ago=days_ago)

    expect_len = len(creative_ids) / googleads.dfp.SUGGESTED_PAGE_LIMIT
    if len(creative_ids) % googleads.dfp.SUGGESTED_PAGE_LIMIT != 0:
      expect_len += 1

    assert len(statements) == expect_len

    for i in xrange(0, len(statements)):
      stmt = statements[i]
      date_setting = ''
      if only_new:
        date_setting = 'lastModifiedDateTime > :date AND'
      id_str = ','.join(str(i) for i in creative_ids)

      assert stmt['query'] == 'WHERE %s id IN (%s) LIMIT %d OFFSET %d' % (date_setting, id_str, googleads.dfp.SUGGESTED_PAGE_LIMIT, googleads.dfp.SUGGESTED_PAGE_LIMIT * i)

  def test_create_report_service_job(self):
    """
    Test the create_report_service_job method with default options.
    """
    self.create_report_service_job()

  def test_create_report_service_job_5_days_ago(self):
    """
    Test the report_service_job method for 5 days ago.
    """
    self.create_report_service_job(days_ago=5)

  def test_create_report_service_job_with_country(self):
    """
    Test the report_service_job method with a country.
    """
    self.create_report_service_job(country='Netherlands')

  def test_create_report_service_job_with_countries(self):
    """
    Test the report_service_job method with countries.
    """
    self.create_report_service_job(country='Netherlands,Germany')

  def test_create_creative_service_statement(self):
    """
    Test the create_creative_service_statement method with default options.
    """
    self.create_creative_service_statement([1])

  def test_create_creative_service_statement_with_only_new(self):
    """
    Test the create_creative_service_statement method with the only_new option.
    """
    self.create_creative_service_statement([1], only_new=True)

  def test_create_creative_service_statement_with_multiple_creatives(self):
    """
    Test the create_creative_service_statement method with multiple creative ids.
    """
    self.create_creative_service_statement([i for i in xrange(0, 1000)])
