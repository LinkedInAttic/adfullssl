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
Scanner that executes the following steps below. You can skip the steps by
setting False to the corresponding item in config.ini.

1. download_new_creative_ids
   This step downloads the IDs of recently-served creatives from DFP. The IDs
   are saved in the creative table in the database.

2. download_creatives
   This steps downloads the creatives corresponding to the IDs downloaded in
   the previous step, and modfies them to become SSL compliant. The creatives
   are stored into the database.

   Since it takes long time to download creatives from DFP, we reuse the
   previously-downloaded creatives in the database if possible. With this
   strategy, this download step runs:

     a) Download the recently updated creatives from DFP
     b) For creatives not downloaded in a), fetch them from the database.
     c) For creatives not found in b), download them from DFP

   The downloaded creatives are stored in the database so that we can reuse
   them next time.

3. browse_creatives
   The creatives are hosted on SSL servers and viewed by browsers. All requests
   and responses are captured for the analysis in the next step.

4. browse_creatives_over_http
   Similar to the previous step, but this step serves the creatives on HTTP
   servers. The network logs are used as a hint for detecting the SSL non-
   compliant creatives in the next step.

5. check_compliance
   This steps analyzes the network logs to detect SSL non-compliant creatives,
   and save the SSL compliance into the databse.

6. upload_creatives
   The creatives are uploaded to DFP if they will become SSL compliant after
   the modification.

7. compress_log_file
   Compress the network log file at the end of the scanning process.

8. remove_temp_files
   Delete the all files under the temporary directory.
"""

import os.path
import datetime

from sqlalchemy import func

import adscan.db
import adscan.dfp
import adscan.fs
import adscan.net
import adscan.transform
from adscan.issue import IssueType
from adscan.xvfb import XvfbController
from adscan.server import ServerController
from adscan.browser import BrowserController
from adscan.model import Creative, ScanLog
from adscan.workspace import Workspace


class Scanner(object):
  """
  Class that detect SSL non-compliant creatives.
  """

  CONF_STEPS = 'Steps'
  CONF_DIRS = 'Directories'
  CONF_LOGS = 'Logs'
  CONF_BROWSER = 'Browser'
  CONF_SERVER = 'Server'
  CONF_MISCS = 'Miscs'

  def __init__(self, config):
    """
    Initialize the scanner.
    """
    self.config = config

    # Directories
    self.logroot_dir = self.config.get(self.CONF_DIRS, 'logroot_dir')
    self.tmp_dir = self.config.get(self.CONF_DIRS, 'tmp_dir')

    # Logs
    self.creative_db = self.config.get(self.CONF_LOGS, 'creative_db')

    # Browser
    self.browser_count = self.config.getint(self.CONF_BROWSER, 'browser_count')
    self.phantomjs = self.config.get(self.CONF_BROWSER, 'phantomjs')
    self.browserjs = self.config.get(self.CONF_BROWSER, 'browserjs')
    self.display_dimension = self.config.get(self.CONF_BROWSER, 'display_dimension')
    self.cookie_dir = self.config.get(self.CONF_BROWSER, 'cookie_dir')
    self.save_netlog = self.config.get(self.CONF_BROWSER, 'save_netlog')

    # Server
    self.server_count = self.config.getint(self.CONF_SERVER, 'server_count')
    self.certificate_file = self.config.get(self.CONF_SERVER, 'certificate_file')
    self.privatekey_file = self.config.get(self.CONF_SERVER, 'privatekey_file')

    # Miscs
    self.days_ago = self.config.getint(self.CONF_MISCS, 'days_ago')
    self.country = self.config.get(self.CONF_MISCS, 'country')
    self.max_scan = self.config.getint(self.CONF_MISCS, 'max_scan')

    dirname = datetime.date.today().strftime('%Y%m%d')
    self.log_dir = os.path.join(self.logroot_dir, dirname)

    self.workspace = None
    self.db_session = None
    self.debug = False

  def _update_creatives(self, creative_ids, values):
    """
    Update creaives in the database. We need to construct a sql because criteria does not accept so many entries in 'IN' statement.

    :param creative_ids: a list of creative ids.
    :param values: a dict of data to be updaed in the database.
    """
    date = datetime.date.today().strftime('%Y-%m-%d')
    ids = ','.join([str(i) for i in creative_ids])
    self.db_session.execute(
      'UPDATE %s SET %s where created_at = \'%s\' AND creative_id IN (%s)' % (Creative.__tablename__, values, date, ids)
    )

  def setup_environment(self):
    """
    Create directories and database used for the scan.
    """
    # Reduce the numbers of servers and browsers if the max_scan value is small.
    if self.max_scan > 0:
      if self.max_scan < self.server_count:
        self.server_count = self.max_scan
      if self.max_scan < self.browser_count:
        self.browser_count = self.max_scan

    adscan.fs.makedirs(self.log_dir)

    self.workspace = Workspace(self.tmp_dir, self.browser_count)
    self.workspace.create()

    self.db_session = adscan.db.new_session(self.creative_db, [Creative, ScanLog])

  def scanlog(self, creative_id, issue_id, protocol, url=None):
    """
    A function to add a scan log to the database. This function does not commit the change.

    :param creative_id: a creative id.
    :param issue_id: an issue id defined in :class:`adscan.issue.IssueType`.
    :param protocol: an HTTP protocol, `https` or `http`.
    :param url: a URL.
    """
    scanlog = ScanLog(creative_id=creative_id, issue_id=issue_id, protocol=protocol, url=url)
    self.db_session.add(scanlog)

  def download_new_creative_ids(self):
    """
    Download the IDs of recently-served creatives from DFP. The IDs are saved in the creative
    table in the database.
    """
    report_job = adscan.dfp.create_report_service_job(self.days_ago, self.country)
    data = adscan.dfp.run_report_service_job(report_job)
    if data:
      # Skip the header line. We only collect creative ids.
      for row in data.split('\n')[1:]:

        # Each row contains a pair of creative id and its impressions. They are delimited with a comma.
        parts = row.split(',')
        if len(parts) > 0 and parts[0]:
          creative_id = parts[0]
          creative = Creative(creative_id=creative_id, created_at=datetime.date.today())
          self.db_session.merge(creative)
      self.db_session.commit()

  def download_creatives(self):
    """
    Downloads the creatives corresponding to the IDs downloaded in the previous step, and modfies
    them to become SSL compliant. The original creatives and modified ones are both stored in the
    database.
    """
    # Load creatives from the database.
    query = self.db_session.query(
      Creative
    ).filter(
      Creative.created_at == datetime.date.today()
    )
    if self.max_scan > 0:
      query = query.limit(self.max_scan)

    creative_list = query.all()
    creative_dict = {}
    for creative in creative_list:
      creative_dict[str(creative.creative_id)] = creative
    print '%d creatives will be scanned.' % len(creative_list)

    # The ids of creatives to be downloaded or fetched from cache.
    remaining_ids = [creative.creative_id for creative in creative_list]

    # Download recently updated creatives.
    if len(remaining_ids) > 0:
      stmts = adscan.dfp.create_creative_service_statement(remaining_ids, days_ago=self.days_ago)
      dfp_creatives = adscan.dfp.run_creative_service_statements(stmts)
      updated = [adscan.transform.from_dfp(dfp) for dfp in dfp_creatives]
      for creative in updated:
        creative_dict[str(creative.creative_id)].merge(creative)
      print '%d recently updated creatives were downloaded.' % len(updated)

      updated_ids = [creative.creative_id for creative in updated]
      remaining_ids = list(set(remaining_ids) - set(updated_ids))

    # Load from cache.
    if len(remaining_ids) > 0:
      ids = ','.join([str(i) for i in remaining_ids])
      caches = self.db_session.query(
        Creative
      ).from_statement(
        'select c.* from %s c join '
        '(select creative_id, max(created_at) as created_at from %s where creative_id in (%s) and snippet is not null group by creative_id) t '
        'on c.creative_id = t.creative_id and c.created_at = t.created_at' % (Creative.__tablename__, Creative.__tablename__, ids)
      ).all()

      for cache in caches:
        creative = adscan.transform.renew(cache)
        creative_dict[str(cache.creative_id)].merge(creative)
      print '%d creatives were loaded from cache.' % len(caches)

      # TemplateCreative should be downloaded to create modified snippet.
      cache_ids = [cache.creative_id for cache in caches if cache.creative_type != 'TemplateCreative']
      remaining_ids = list(set(remaining_ids) - set(cache_ids))

    # Download creatives that did not in the cache.
    if len(remaining_ids) > 0:
      stmts = adscan.dfp.create_creative_service_statement(remaining_ids, days_ago=self.days_ago, only_new=False)
      dfp_creatives = adscan.dfp.run_creative_service_statements(stmts)
      refetched = [adscan.transform.from_dfp(dfp) for dfp in dfp_creatives]
      for creative in refetched:
        creative_dict[str(creative.creative_id)].merge(creative)
      print '%d creative were downloaded.' % len(refetched)

    self.db_session.commit()

  def browse_creatives(self, protocol):
    """
    The creatives are hosted on SSL servers and viewed by browsers. All requests and responses are
    captured for the analysis in the next step.

    :param protocol: `https` or `http`.
    """
    if not os.path.exists(self.certificate_file):
      raise Exception('No certificate found.')
    if not os.path.exists(self.privatekey_file):
      raise Exception('No private key found.')

    # Delete the existing scanlog.
    self.db_session.query(
      ScanLog
    ).filter(
      ScanLog.created_at == datetime.date.today(),
      ScanLog.protocol == protocol
    ).delete()

    query = self.db_session.query(
      Creative
    ).filter(
      Creative.created_at == datetime.date.today()
    )

    if self.max_scan > 0:
      query = query.limit(self.max_scan)

    creatives = query.all()
    servers, xvfbs, browsers = None, None, None

    try:
      # Open ports and bind them to servers.
      ports = adscan.net.find_open_ports(self.server_count)
      servers = ServerController(protocol, ports, self.certificate_file, self.privatekey_file)
      servers.start()

      # Start virtual X windows.
      xvfbs = XvfbController(self.browser_count, self.display_dimension)
      xvfbs.start()

      # Start browsers
      browsers = BrowserController(
        creatives, protocol, ports, self.browser_count, self.phantomjs, self.browserjs, self.cookie_dir,
        self.workspace.dirname, self.scanlog, adscan.transform.create_scan_snippet, self.debug)
      browsers.start()
      browsers.wait()
    except KeyboardInterrupt:
      raise
    finally:
      if browsers:
        browsers.shutdown()
      if servers:
        servers.shutdown()
      if xvfbs:
        xvfbs.shutdown()

    self.db_session.commit()

    if self.save_netlog:
      dest_dir = '%s/%s/netlog' % (self.log_dir, protocol)
      self.workspace.move_netlog(dest_dir)

  def check_compliance(self):
    """
    Analyzes the network logs to detect SSL non-compliant creatives, and save the SSL compliance
    into the databse.
    """
    def request_count(protocol):
      """
      Return the numver of requests for each creatives.

      :param protocol: 'https' or 'http'.
      :return: a tuple of creative id and the number of requests.
      """
      return self.db_session.query(
        ScanLog.creative_id.label('creative_id'),
        func.count(ScanLog.url).label('url_count')
      ).filter(
        ScanLog.created_at == datetime.date.today(),
        ScanLog.protocol == protocol
      ).group_by(
        ScanLog.creative_id
      ).subquery(protocol)

    def request_match_ids():
      """
      Return the ids of creatives that made difference numbers of requests over https and http.
      """
      https = request_count('https')
      http = request_count('http')

      return [t[0] for t in self.db_session.query(
        https.c.creative_id
      ).filter(
        https.c.creative_id == http.c.creative_id,
        https.c.url_count == http.c.url_count
      ).all()]

    creative_ids = [t[0] for t in self.db_session.query(
      ScanLog.creative_id
    ).filter(
      ScanLog.created_at == datetime.date.today()
    ).distinct().all()]
    print '# of creatives: %d' % len(creative_ids)

    noncompliant_ids = [t[0] for t in self.db_session.query(
      ScanLog.creative_id
    ).filter(
      ScanLog.created_at == datetime.date.today(),
      ScanLog.issue_id != IssueType.NO_ISSUE,
      ScanLog.issue_id != IssueType.NO_EXTERNAL,
      ScanLog.issue_id is not None,
      ScanLog.protocol == 'https'
    ).distinct().all()]

    compliant_ids = list(set(creative_ids) - set(noncompliant_ids))
    print '# of compliant: %d' % len(compliant_ids)
    print '# of non-compliant: %d' % len(noncompliant_ids)

    match_ids = request_match_ids()
    unmatch_ids = list(set(creative_ids) - set(match_ids))
    print '# of request match: %d' % len(match_ids)
    print '# of request unmatch: %d' % len(unmatch_ids)

    # Update the compliance status.
    if len(compliant_ids) > 0:
      self._update_creatives(compliant_ids, 'compliance=1')
    if len(noncompliant_ids) > 0:
      self._update_creatives(noncompliant_ids, 'compliance=0')

    # Update the request match status.
    if len(match_ids) > 0:
      self._update_creatives(match_ids, 'request_match=1')
    if len(unmatch_ids) > 0:
      self._update_creatives(unmatch_ids, 'request_match=0')

    self.db_session.commit()

  def upload_creatives(self):
    """
    Upload the creatives to DFP if they become SSL compliant after the modification.
    """
    creatives = self.db_session.query(
      Creative
    ).filter(
      Creative.created_at == datetime.date.today(),
      Creative.modified,
      Creative.compliance,
      Creative.request_match,
      Creative.modified_snippet is not None
    ).all()

    creative_ids = [creative.creative_id for creative in creatives]

    # Modify creatives.
    if len(creative_ids) > 0:
      creative_dict = {}
      for creative in creatives:
        creative_dict[str(creative.creative_id)] = creative

      stmts = adscan.dfp.create_creative_service_statement(creative_ids, only_new=False)
      dfp_creatives = adscan.dfp.run_creative_service_statements(stmts)
      modified_dfp = [adscan.transform.to_dfp(creative_dict[str(dfp['id'])], dfp) for dfp in dfp_creatives]

      # Upload the modified creatives.
      updated = adscan.dfp.upload_creatives(modified_dfp)
      print '%d creatives were modified.' % len(updated)
      self._update_creatives(creative_ids, 'uploaded=1')

  def compress_log_file(self):
    """
    Compress the network log file at the end of the scanning process.
    """
    cwd = os.getcwd()
    os.chdir(self.logroot_dir)

    dirname = os.path.split(self.log_dir)[-1]

    tarfile = '%s.tgz' % dirname
    adscan.fs.tar(tarfile, dirname)
    adscan.fs.rmdirs(dirname)

    os.chdir(cwd)

  def remove_temp_files(self):
    """
    Delete the all files under the temporary directory.
    """
    self.workspace.delete()
