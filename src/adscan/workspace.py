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
Workspace that temporarily stores browsers' log files.
"""

import os
import os.path
import shutil

import adscan.fs


class Workspace(object):
  """
  Class that indicates the browser workspace used in adscan.
  """

  def __init__(self, dirname, browser_space_size):
    """
    Initialize an instance.

    :param dirname: the path to the workspace directory.
    :param size: Number of working spaces created by `create` method of this object.
    """
    self.dirname = dirname
    self.browser_space_size = browser_space_size

  def create(self):
    """
    Create the browser workspace.
    """
    adscan.fs.makedirs(self.dirname)

    for i in xrange(0, self.browser_space_size):
      dirname = '%s/%d' % (self.dirname, i)
      adscan.fs.makedirs(dirname)

  def delete(self):
    """
    Delete the browser workspace.
    """
    adscan.fs.rmdirs(self.dirname)

  def move_netlog(self, dest_dir):
    """
    Move the scan logs to another location.

    :param dest_dir: Path to the directory the log is saved.
    """
    if os.path.exists(dest_dir):
      adscan.fs.rmdirs(dest_dir)
    adscan.fs.makedirs(dest_dir)

    for i in xrange(0, self.browser_space_size):
      src = '%s/%d' % (self.dirname, i)
      for fp in os.listdir(src):
        if fp.endswith('.json'):
          path = os.path.join(src, fp)
          dest_file = os.path.join(dest_dir, fp)
          if os.path.exists(dest_file):
            os.remove(dest_file)
          shutil.move(path, dest_dir)
