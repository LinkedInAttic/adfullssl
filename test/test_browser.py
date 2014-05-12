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

import re
import os
import json
import socket
import shutil
import unittest
import datetime
from ConfigParser import SafeConfigParser

import adscan.fs
import adscan.net
from adscan.model import Creative
from adscan.scanner import Scanner


CONFIG_FILE = 'config.ini'
TEST_RESOURCE = 'test/resources'


class BrowserTestCase(unittest.TestCase):
  """
  Test the browser controller.
  """

  @classmethod
  def copy_resources(cls, dest):
    """
    Copy resource files to the
    """
    for fp in os.listdir(TEST_RESOURCE):
      path = os.path.join(TEST_RESOURCE, fp)
      if (os.path.isfile(path)):
        shutil.copy(path, dest)

  def setUp(self):
    """
    Load the scanner, which helps to set up the test environment.
    """
    # Move to the project directory.
    project_dir = os.path.join(os.path.dirname(__file__), os.pardir)
    os.chdir(project_dir)

    conf_file = os.path.join('conf', CONFIG_FILE)
    config = SafeConfigParser()
    config.read(conf_file)

    self.scanner = Scanner(config)
    self.scanner.log_dir = os.path.join(self.scanner.logroot_dir, 'testlog')
    self.scanner.tmp_dir = 'testtmp'
    self.scanner.creative_db = 'sqlite:///%s/creative.db' % self.scanner.log_dir
    self.scanner.max_scan = 1

    self.scanner.setup_environment()
    self.copy_resources(self.scanner.workspace.dirname)

    self.hostname = socket.gethostname()

  def tearDown(self):
    """
    Delete the exising processes and clear the directory.
    """
    adscan.fs.rmdirs(self.scanner.log_dir)
    self.scanner.workspace.delete()

  def _browse_creative(self, creative_id, snippet):
    """
    Set up a server and a browser to view the snippet.
    """
    creatives = self.scanner.db_session.query(
        Creative
      ).filter(
        Creative.created_at == datetime.date.today(),
        Creative.creative_id == creative_id
      ).all()
    if creatives and len(creatives) > 0:
      self.scanner.db_session.delete(creatives[0])
      self.scanner.db_session.commit()

    creative = Creative(creative_id=creative_id, snippet=snippet)
    self.scanner.db_session.add(creative)
    self.scanner.db_session.commit()

    self.scanner.browse_creatives('https')

    self.scanner.db_session.delete(creative)
    self.scanner.db_session.commit()

    netlog = None
    logfile = '%s/https/netlog/%d.json' % (self.scanner.log_dir, creative_id)
    with open(logfile, 'r') as fp:
      netlog = json.load(fp)
    return netlog

  def test_browser_view_image(self):
    """
    Test if the browser can view an image.
    """
    creative_id = 11111
    snippet = '<img src="pixel.png">'

    netlog = self._browse_creative(creative_id, snippet)
    path1 = r'https\:\/\/%s\:\d+\/%s\/%s\.html' % (re.escape(self.hostname), re.escape(self.scanner.workspace.dirname), creative_id)
    path2 = r'https\:\/\/%s\:\d+\/%s\/pixel\.png' % (re.escape(self.hostname), re.escape(self.scanner.workspace.dirname))

    assert netlog
    assert len(netlog) == 2
    assert re.match(path1, netlog['1']['request']['url'])
    assert netlog['1']['response']['status'] == 200
    self.assertFalse(netlog['1']['error'])

    assert re.match(path2, netlog['2']['request']['url'])
    assert netlog['2']['response']['status'] == 200
    self.assertFalse(netlog['2']['error'])

  def test_browser_with_error_code(self):
    """
    Test if the browser can catch 404 error code.
    """
    creative_id = 11111
    snippet = '<img src="notfound.png">'

    netlog = self._browse_creative(creative_id, snippet)
    path1 = r'https\:\/\/%s\:\d+\/%s\/%s\.html' % (re.escape(self.hostname), re.escape(self.scanner.workspace.dirname), creative_id)
    path2 = r'https\:\/\/%s\:\d+\/%s\/notfound\.png' % (re.escape(self.hostname), re.escape(self.scanner.workspace.dirname))

    assert netlog
    assert len(netlog) == 2
    assert re.match(path1, netlog['1']['request']['url'])
    assert netlog['1']['response']['status'] == 200
    self.assertFalse(netlog['1']['error'])

    assert re.match(path2, netlog['2']['request']['url'])
    assert netlog['2']['response']['status'] == 404
    assert netlog['2']['error']['errorCode'] == 203

  def test_browser_with_no_external_request(self):
    """
    Test if the browser does not make unintended requests.
    """
    creative_id = 11111
    snippet = '<b>text</b>'

    netlog = self._browse_creative(creative_id, snippet)
    path1 = r'https\:\/\/%s\:\d+\/%s\/%s\.html' % (re.escape(self.hostname), re.escape(self.scanner.workspace.dirname), creative_id)

    assert netlog
    assert len(netlog) == 1
    assert re.match(path1, netlog['1']['request']['url'])
    assert netlog['1']['response']['status'] == 200
    self.assertFalse(netlog['1']['error'])

  def test_browser_with_requests_made_by_flash(self):
    """
    Test if the browser can catch requests made by a flash content.
    """
    creative_id = 11111
    flash = 'request_pixel.swf'
    snippet = " <object classid='clsid:D27CDB6E-AE6D-11cf-96B8-444553540000' " \
              " codebase='http://download.macromedia.com/pub/shockwave/cabs/flash/swflash.cab#version=6,0,0,0' " \
              " width='300' height='250'> " \
              " <param name='movie' value='%s'> " \
              " <param name='quality' value='high'> " \
              " <param name='bgcolor' value='#ffffff'> " \
              " <embed src='%s' quality='high' bgcolor='#ffffff' width='300' height='250' " \
              " type='application/x-shockwave-flash' pluginpage='http://www.macromedia.com/go/getflashplayer'></embed> " \
              " </object> " % (flash, flash)

    netlog = self._browse_creative(creative_id, snippet)
    path1 = r'https\:\/\/%s\:\d+\/%s\/%s\.html' % (re.escape(self.hostname), re.escape(self.scanner.workspace.dirname), creative_id)
    path2 = r'https\:\/\/%s\:\d+\/%s\/request_pixel\.swf' % (re.escape(self.hostname), re.escape(self.scanner.workspace.dirname))
    path3 = r'https\:\/\/%s\:\d+\/%s\/pixel\.png' % (re.escape(self.hostname), re.escape(self.scanner.workspace.dirname))

    assert netlog
    assert len(netlog) == 3
    assert re.match(path1, netlog['1']['request']['url'])
    assert netlog['1']['response']['status'] == 200
    self.assertFalse(netlog['1']['error'])

    assert re.match(path2, netlog['2']['request']['url'])
    assert netlog['2']['response']['status'] == 200
    self.assertFalse(netlog['2']['error'])

    assert re.match(path3, netlog['3']['request']['url'])
    assert netlog['3']['response']['status'] == 200
    self.assertFalse(netlog['3']['error'])

  def test_browser_with_url_snippet(self):
    """
    Test if the browser sends a request to the url if the snippet is a url.
    """
    creative_id = 11111
    snippet = 'https://invalidurl/nocontent'

    netlog = self._browse_creative(creative_id, snippet)
    path1 = re.escape(snippet)

    assert netlog
    assert len(netlog) == 1
    assert re.match(path1, netlog['1']['request']['url'])

  def test_browser_with_private_network(self):
    """
    Test if the browser blocks a request to a private network.
    When the request is aborted, PhantomJS will set 1 (Connection Refused Error) for the error code.
    """
    creative_id = 11111
    snippet = '<img src="https://localhost:8888/pixel.png">'

    netlog = self._browse_creative(creative_id, snippet)
    path1 = r'https\:\/\/%s\:\d+\/%s\/%s\.html' % (re.escape(self.hostname), re.escape(self.scanner.workspace.dirname), creative_id)
    path2 = r'https\:\/\/localhost\:8888\/pixel\.png'

    assert netlog
    assert len(netlog) == 2
    assert re.match(path1, netlog['1']['request']['url'])
    assert netlog['1']['response']['status'] == 200
    self.assertFalse(netlog['1']['error'])

    assert re.match(path2, netlog['2']['request']['url'])
    assert netlog['2']['response']['status'] is None
    assert netlog['2']['error']['errorCode'] == 1  # ConnectionRefusedError

  def test_browser_with_private_network_with_ip_url(self):
    """
    Test if the browser blocks a request to a private network.
    When IP address is used, PhantomJS will set 301 (Protocol Unknown Error) for the error code.
    """
    creative_id = 11111
    snippet = '<img src="http://172.21.78.62/pixel.png">'

    netlog = self._browse_creative(creative_id, snippet)
    path1 = r'https\:\/\/%s\:\d+\/%s\/%s\.html' % (re.escape(self.hostname), re.escape(self.scanner.workspace.dirname), creative_id)
    path2 = r'http\:\/\/172\.21\.78\.62\/pixel\.png'

    assert netlog
    assert len(netlog) == 2
    assert re.match(path1, netlog['1']['request']['url'])
    assert netlog['1']['response']['status'] == 200
    self.assertFalse(netlog['1']['error'])

    assert re.match(path2, netlog['2']['request']['url'])
    assert netlog['2']['response']['status'] is None
    assert netlog['2']['error']['errorCode'] == 301  # ProtocolUnknownError
