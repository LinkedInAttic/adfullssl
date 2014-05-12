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
Class that defines issue types.
"""

class IssueType(object):
  """
  Class that represents issue types.
  """

  NO_ISSUE = 0
  INVALID_CERT = 1
  NO_SSL_SERVER = 2
  HTTPS_AVAIL = 3
  CLIENT_ERROR = 4
  SERVER_ERROR = 5
  PRIVATE_NETWORK = 8
  NO_EXTERNAL = 9

  def __init__(self):
    pass
