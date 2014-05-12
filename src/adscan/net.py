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
Utility functions that handles networks.
"""

import socket


def find_open_ports(num):
  """
  Find open port numbers.

  :param num: the number of ports to find.
  :return: a list of open port numbers.
  """
  def _find_port():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('', 0))
    port = sock.getsockname()[1]
    sock.close()
    return port

  ports = []
  trial_limit = 10
  for i in xrange(0, num):
    trial = 0
    while True:
      port = _find_port()
      if not port in ports:
        ports.append(port)
        break
      elif trial >= trial_limit:
        break
      else:
        trial += 1
  return ports
