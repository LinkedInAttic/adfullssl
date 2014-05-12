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

import os
import os.path
import unittest
from ConfigParser import SafeConfigParser

import adscan.fs
from adscan.scanner import Scanner


CONFIG_FILE = 'config.ini'


class ScannerTestCase(unittest.TestCase):
  """
  Test the scanner module.
  """

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
    self.scanner.setup_environment()

  def tearDown(self):
    """
    Delete the exising processes and clear the directory.
    """
    adscan.fs.rmdirs(self.scanner.log_dir)
    self.scanner.workspace.delete()

  def test_no_certificate(self):
    """
    Test if an exception is throws when no certificate is set at the browse_creatives step.
    """
    original_cert = self.scanner.certificate_file
    self.scanner.certificate_file = None
    self.assertRaises(Exception, self.scanner.browse_creatives, 'https')
    self.scanner.certificate_file = 'cert.pem'
    self.assertRaises(Exception, self.scanner.browse_creatives, 'https')
    self.scanner.certificate_file = original_cert

  def test_no_privatekey(self):
    """
    Test if an exception is throws when no private key is set at the browse_creatives step.
    """
    original_pkey = self.scanner.privatekey_file
    self.scanner.privatekey_file = None
    self.assertRaises(Exception, self.scanner.browse_creatives, 'https')
    self.scanner.privatekey_file = 'pkey.pem'
    self.assertRaises(Exception, self.scanner.browse_creatives, 'https')
    self.scanner.privatekey_file = original_pkey

  def test_setup_environment_and_remove_temp_files(self):
    """
    Test if the temporary files are deleted.
    """
    conf_file = os.path.join('conf', CONFIG_FILE)
    config = SafeConfigParser()
    config.read(conf_file)

    scanner = Scanner(config)
    scanner.log_dir = os.path.join(scanner.logroot_dir, 'test_remove_temp_files')
    scanner.tmp_dir = 'test_remove_temp_files'
    scanner.creative_db = 'sqlite:///%s/creative.db' % scanner.log_dir

    scanner.setup_environment()
    assert os.path.exists(scanner.workspace.dirname)

    scanner.remove_temp_files()
    self.assertFalse(os.path.exists(scanner.workspace.dirname))

    adscan.fs.rmdirs(scanner.log_dir)
    adscan.fs.rmdirs(scanner.tmp_dir)

  def test_compress_log_file(self):
    """
    Test if the log file is compressed.
    """
    conf_file = os.path.join('conf', CONFIG_FILE)
    config = SafeConfigParser()
    config.read(conf_file)

    scanner = Scanner(config)
    scanner.log_dir = os.path.join(scanner.logroot_dir, 'test_compress_log_file')

    tarname = '%s.tgz' % scanner.log_dir

    scanner.setup_environment()
    assert os.path.exists(scanner.log_dir)
    if os.path.exists(tarname):
      os.remove(tarname)

    scanner.compress_log_file()
    assert os.path.exists(tarname)

    adscan.fs.rmdirs(scanner.log_dir)
    os.remove(tarname)
