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
Classes for database schema.
"""

from datetime import date

from sqlalchemy import event
from sqlalchemy import Column, Integer, String, Date, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


def before_insert_listener(mapper, connection, instance):
  """
  Set the current date to created_at.
  """
  instance.created_at = date.today()


def before_update_listener(mapper, connection, instance):
  """
  set the current date updated_at.
  """
  instance.updated_at = date.today()


class Creative(Base):
  """
  Class that represents a creative.
  """
  __tablename__ = 'creative'

  created_at = Column(Date, primary_key=True)
  updated_at = Column(Date)
  creative_id = Column(Integer, primary_key=True)
  creative_type = Column(String)
  preview_url = Column(String)
  modified = Column(Boolean)
  snippet = Column(String)
  modified_snippet = Column(String)
  expanded_snippet = Column(String)
  compliance = Column(Boolean)
  request_match = Column(Boolean)
  uploaded = Column(Boolean)

  # Fields not stored in the database
  modified_expanded_snippet = None
  scan_snippet = None
  modified_scan_snippet = None

  def merge(self, creative):
    """
    Need to merge each field manually because the merge() method will generate error
    due to the composite primary used in this table if the value already exists.

    :param creative: the creative of which data is merged to this object.
    """
    self.creative_type = creative.creative_type
    self.preview_url = creative.preview_url
    self.modified = creative.modified
    self.snippet = creative.snippet
    self.modified_snippet = creative.modified_snippet
    self.expanded_snippet = creative.expanded_snippet


event.listen(Creative, 'before_insert', before_insert_listener)
event.listen(Creative, 'before_update', before_update_listener)


class ScanLog(Base):
  """
  Class that represents a request log made by a browser.
  """
  __tablename__ = 'scanlog'

  id = Column(Integer, primary_key=True, autoincrement=True)
  created_at = Column(Date)
  updated_at = Column(Date)
  creative_id = Column(Integer)
  issue_id = Column(Integer)
  url = Column(String)
  protocol = Column(String)


event.listen(ScanLog, 'before_insert', before_insert_listener)
event.listen(ScanLog, 'before_update', before_update_listener)
