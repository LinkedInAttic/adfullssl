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

import time
import unittest

from adscan.xvfb import XvfbController


class XvfbTestCase(unittest.TestCase):
  """
  Test the xvfb module.
  """

  def test_run_and_shutdown(self):
    """
    Create multiple xvfb and shut them down.
    """
    num = 10
    dimensions = '1024x768x24'
    xvfbs = XvfbController(num, dimensions)
    xvfbs.start()

    for process in xvfbs.processes:
      assert process.poll() is None

    xvfbs.shutdown()

    time.sleep(1)

    for process in xvfbs.processes:
      assert process.poll()
