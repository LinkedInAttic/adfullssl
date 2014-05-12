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
import socket
import unittest
from ConfigParser import SafeConfigParser

import adscan.net
from adscan.server import Server

CONFIG_FILE = 'config.ini'


class ServerTestCase(unittest.TestCase):
  """
  Test the server module.
  """

  def setUp(self):
    """
    Use the server settings defined in config.ini.
    """
    # Move to the project directory.
    project_dir = os.path.join(os.path.dirname(__file__), os.pardir)
    os.chdir(project_dir)

    conf_file = os.path.join('conf', CONFIG_FILE)
    config = SafeConfigParser()
    config.read(conf_file)

    self.certificate_file = config.get('Server', 'certificate_file')
    self.privatekey_file = config.get('Server', 'privatekey_file')

  def test_run_server(self):
    """
    Create the server and start the process.
    """
    ports = adscan.net.find_open_ports(1)
    server = Server('https', ports[0], self.certificate_file, self.privatekey_file)

    server.start()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.assertRaises(socket.error, sock.bind, ('', ports[0]))
    server.shutdown()
