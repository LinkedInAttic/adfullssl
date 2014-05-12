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
Functions to launch a new scanning process.
"""

import sys
import os.path
from ConfigParser import SafeConfigParser

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))

from adscan.scanner import Scanner


CONFIG_FILE = 'config.ini'


def get_boolean(config, section, option):
  """
  Return the boolean value set inside of the section -> option in the config.

  :param config: the config parser.
  :param section: a string that represents the section in the config file.
  :param option: a string that represents the option in the config file.
  :return: the boolean value.
  """
  return config.has_option(section, option) and config.getboolean(section, option)


def main():
  """
  The main method to launch the scanner.
  """
  # Move to the project directory.
  project_dir = os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
  os.chdir(project_dir)

  conf_file = os.path.join('conf', CONFIG_FILE)
  config = SafeConfigParser()
  config.read(conf_file)

  scanner = Scanner(config)
  scanner.setup_environment()

  if get_boolean(config, 'Steps', 'download_new_creative_ids'):
    scanner.download_new_creative_ids()

  if get_boolean(config, 'Steps', 'download_creatives'):
    scanner.download_creatives()

  if get_boolean(config, 'Steps', 'browse_creatives'):
    scanner.browse_creatives('https')

  if get_boolean(config, 'Steps', 'browse_creatives_over_http'):
    scanner.browse_creatives('http')

  if get_boolean(config, 'Steps', 'check_compliance'):
    scanner.check_compliance()

  if get_boolean(config, 'Steps', 'upload_creatives'):
    scanner.upload_creatives()

  if get_boolean(config, 'Steps', 'compress_log_file'):
    scanner.compress_log_file()

  if get_boolean(config, 'Steps', 'remove_temp_files'):
    scanner.remove_temp_files()

  sys.exit(0)


if __name__ == "__main__":
  main()
