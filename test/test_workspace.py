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

import adscan.fs
from adscan.workspace import Workspace


class WorkspaceTestCase(unittest.TestCase):
  """
  Test the transform module.
  """

  WORK_DIR = '__workspace_test__'
  WORKSPACE = 'workspace'

  def setUp(self):
    """
    Create the working directory and move into it.
    """
    self.default_dir = os.getcwd()
    adscan.fs.makedirs(self.WORK_DIR)
    os.chdir(self.WORK_DIR)

  def tearDown(self):
    """
    Exit from the working directory and remove it.
    """
    os.chdir(self.default_dir)
    adscan.fs.rmdirs(self.WORK_DIR)

  def test_create(self):
    """
    Test to delete workspace.
    """
    num = 10
    workspace = Workspace(self.WORKSPACE, num)
    workspace.create()
    for i in xrange(0, num):
      assert os.path.exists('%s/%d' % (self.WORKSPACE, i))
    workspace.delete()
    self.assertFalse(os.path.exists(self.WORKSPACE))

  def test_delete(self):
    """
    Test to delete workspace.
    """
    workspace = Workspace(self.WORKSPACE, 1)
    workspace.create()
    assert os.path.exists(self.WORKSPACE)
    workspace.delete()
    self.assertFalse(os.path.exists(self.WORKSPACE))

  def test_move_netlog(self):
    """
    Test to move network logs.
    """
    dest_dir = 'dest'
    num = 10
    workspace = Workspace(self.WORKSPACE, num)
    workspace.create()
    for i in xrange(0, num):
      dirname = '%s/%d' % (self.WORKSPACE, i)
      assert os.path.exists(dirname)
      for j in xrange(0, num):
        filename = '%s/%d_%d.json' % (dirname, i, j)
        open(filename, 'a').close()
        assert os.path.exists(filename)
    workspace.move_netlog(dest_dir)
    for i in xrange(0, num):
      for j in xrange(0, num):
        filename = '%s/%d_%d.json' % (dest_dir, i, j)
        assert os.path.exists(filename)
    workspace.delete()
    self.assertFalse(os.path.exists(self.WORKSPACE))
