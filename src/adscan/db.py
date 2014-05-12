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
Utility functions for handling databases.

Requires SQLAlchemy.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def new_session(database, table, drop_if_exist=False):
  """
  Create a new session for the database and the table(s). Create the table(s) if they do not exist yet. Multiple tables
  can be specified.

  :param database: a string that represents the location of database.
  :param table: a string or a list that represents the table(s) to use.
  :param drop_if_exist: a boolean value that indicates the existing table(s) will be dropped if True. Otherwise, the
    table(s) will not be dropped.
  :return: a new session.
  """
  engine = create_engine(database)
  if isinstance(table, list):
    for _table in table:
      create_table(engine, _table, drop_if_exist)
  else:
    create_table(engine, table, drop_if_exist)
  session = sessionmaker(bind=engine)
  return session()


def create_table(engine, table, drop_if_exist=False):
  """
  Create a new table.

  :param engine: a string that represents the location of database.
  :param table: a string that represents the table to create.
  :param drop_if_exist: a boolean value that indicates the existing table will be dropped if True. Otherwise, the table
    will not be dropped.
  """
  if drop_if_exist:
    table.__table__.drop(engine, checkfirst=True)
  table.__table__.create(engine, checkfirst=True)
