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
Launch and close processes of Xvfb (virtual X window system).
"""

import subprocess


class XvfbController(object):
  """
  Class that controls xvfb (virtual X window system).
  """

  def __init__(self, num, dimensions, xserver_offset=1):
    """
    Initiate an instance.

    :param num: the number of xvfb to be launched.
    :param dimensions: the display dimensions.
    :param xserver_offset: an offset number, from which we will reserve IDs of X servers.
    """
    self.num = num
    self.dimensions = dimensions
    self.processes = []
    self.xserver_offset = xserver_offset

  def start(self):
    """
    Create virtual X windows. The display numbers should incremented from 1 because 0 is already used
    by the X window system.
    """
    for i in xrange(1, self.num + 1):
      command = ['Xvfb', ':%d -screen 0 %s' % (self.xserver_offset + i, self.dimensions)]
      process = subprocess.Popen(command, shell=False)
      self.processes.append(process)

  def shutdown(self):
    """
    Stop all the processes.
    """
    for proc in self.processes:
      proc.kill()
