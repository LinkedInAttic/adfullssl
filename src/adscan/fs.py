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
Utility functions for handling file systems.
"""

import os
import os.path
import shutil
import tarfile


def makedirs(path, check=True):
  """
  Create a new directory if it is not existed. The parent directories are also created.

  :param path: the path to the directory to be created.
  :param check: a boolean value that indicates whether the existance of directory is checked or not.
  """
  if check:
    if not os.path.exists(path):
      os.makedirs(path)
  else:
    os.makedirs(path)


def rmdirs(path, check=True):
  """
  Delete the browser workspace. The decendant directories are also deleted if `check` if true.

  :param path: the path to the directory to be deleted.
  :param check: a boolean value that indicates whether the existance of directory is checked or not.
  """
  if check:
    if os.path.exists(path):
      shutil.rmtree(path)
  else:
    shutil.rmtree(path)


def tar(dest_file, src_dir):
  """
  Compress the directory into a single file.

  :param dest_file: the file to be generated.
  :param src_dir: the directory to be compressed.
  """
  if os.path.exists(dest_file):
    os.remove(dest_file)

  tar_file = tarfile.open(dest_file, 'w:gz')
  tar_file.add(src_dir, arcname=os.path.basename(src_dir))
  tar_file.close()
