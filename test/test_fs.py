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


class FileSystemTestCase(unittest.TestCase):
  """
  Test the fs module.
  """

  WORK_DIR = '__fs_test__'

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

  def test_makedirs(self):
    """
    Test to make directories.
    """
    dirname = 'test_makedirs/test_makedirs'
    adscan.fs.makedirs(dirname)
    assert os.path.exists(dirname)

  def test_makedirs_without_check(self):
    """
    Test to make directories without checking the existance.
    """
    dirname = 'test_makedirs_without_check/test_makedirs_without_check'
    adscan.fs.makedirs(dirname)
    assert os.path.exists(dirname)
    self.assertRaises(OSError, adscan.fs.makedirs, dirname, check=False)

  def test_rmdirs(self):
    """
    Test to remove directories.
    """
    dirname = 'test_rmdirs/test_rmdirs'
    adscan.fs.makedirs(dirname)
    assert os.path.exists(dirname)
    adscan.fs.rmdirs(dirname)
    self.assertFalse(os.path.exists(dirname))

  def test_rmdirs_without_check(self):
    """
    Test to remove directories without checking the existance.
    """
    dirname = 'test_rmdirs_without_check/test_rmdirs_without_check'
    if os.path.exists(dirname):
      adscan.fs.rmdirs(dirname)
    self.assertRaises(OSError, adscan.fs.rmdirs, dirname, check=False)

  def test_tar_file(self):
    """
    Test for compress a file with tar.
    """
    filename = 'test_tar_file.txt'
    tarfile = 'test_tar_file.txt.tgz'
    open(filename, 'a').close()
    assert os.path.exists(filename)
    adscan.fs.tar(tarfile, filename)
    assert os.path.exists(tarfile)

  def test_tar_dir(self):
    """
    Test for compress a directory with tar.
    """
    dirname = 'test_tar_dir'
    tarfile = 'test_tar_dir.tgz'
    adscan.fs.makedirs(dirname)
    assert os.path.exists(dirname)
    adscan.fs.tar(tarfile, dirname)
    assert os.path.exists(tarfile)

  def test_tar_file_with_existing_dest(self):
    """
    Test for compress a file with tar. Existing destination should be deleted before making a new file.
    """
    filename = 'test_tar_file_with_existing_dest.txt'
    tarfile = 'test_tar_file_with_existing_dest.txt.tgz'
    open(tarfile, 'a').close()
    assert os.path.exists(tarfile)
    open(filename, 'a').close()
    assert os.path.exists(filename)
    adscan.fs.tar(tarfile, filename)
    assert os.path.exists(tarfile)
