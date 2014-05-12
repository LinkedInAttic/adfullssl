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
Classes that handles servers.
"""

import ssl
import threading
import BaseHTTPServer
import SimpleHTTPServer


class Server(threading.Thread):
  """
  Class that represents a HTTPS or HTTP server.
  """

  def __init__(self, protocol, port, certificate=None, privatekey=None):
    """
    Initiate an instance with the specified protocol, port, and ssl certificates.

    :param protocol: the server protocol, either of 'https'or 'http'.
    :param port: a number that represents a server port.
    :param certificate: the path to the certificate file.
    :param privatekey: the path to the private key file.
    """
    threading.Thread.__init__(self)
    self.protocol = protocol
    self.port = port
    self.certificate = certificate
    self.privatekey = privatekey
    self.httpd = BaseHTTPServer.HTTPServer(('', port), SimpleHTTPServer.SimpleHTTPRequestHandler)
    if protocol == 'https':
      self.httpd.socket = ssl.wrap_socket(self.httpd.socket, certfile=certificate, keyfile=privatekey, server_side=True)

  def run(self):
    """
    Start the server.
    """
    self.httpd.serve_forever()

  def shutdown(self):
    """
    Stop the server.
    """
    self.httpd.shutdown()


class ServerController(object):
  """
  Class that controls multiple servers.
  """

  def __init__(self, protocol, ports, certificate=None, privatekey=None):
    """
    Initiate an instance with the specified protocol, port, and ssl certificates.

    :param protocol: the server protocol, either of 'https'or 'http'.
    :param ports: a list of numbers that will be bound to servers.
    :param certificate: the path to the certificate file.
    :param privatekey: the path to the private key file.
    """
    self.protocol = protocol
    self.ports = ports
    self.certificate = certificate
    self.privatekey = privatekey
    self.threads = []

  def start(self):
    """
    Start multiple servers.

    :return: a list of server threads.
    """
    for port in self.ports:
      server = Server(self.protocol, port, self.certificate, self.privatekey)
      server.start()
      self.threads.append(server)

  def shutdown(self):
    """
    Stop all the servers.
    """
    for thread in self.threads:
      if thread and thread.isAlive():
        thread.shutdown()
