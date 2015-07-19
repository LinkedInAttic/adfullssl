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
Classes that handles browsers to view creatives and analyze the network logs.
"""

import os
import os.path
import re
import json
import time
import socket
import requests
import threading
import subprocess

from adscan.issue import IssueType


class BrowserHost(threading.Thread):
  """
  Class that launches an external PhantomJS process to view multiple urls one by one. The PhantomJS browser is launched
  with an option that accepts any invalid SSL certificates to capture all the requests made by each creative. The PhantomJS
  creates a log file containing the requested urls. By sending a request to each url (again but without ignoring invalid SSL
  certificates), we can check if the urls have any problems or not.
  """

  @classmethod
  def verify_http_url(cls, session, url):
    """
    Check if the url is avaiable over https or not.

    :param session: the session of requests library.
    :param url: the URL found on the log file. Its protocol should be either of http or https.
    :return: an issue id defined in :class:`adscan.issue.IssueType`.
    """
    issue_id = IssueType.NO_ISSUE if re.match(r'^https', url) else IssueType.HTTPS_AVAIL
    try:
      req_url = re.sub(r'^http\:', 'https:', url)
      res = session.get(req_url, verify=True, allow_redirects=True)
      if res.status_code == 403:
        issue_id = IssueType.INVALID_CERT
      if res.status_code >= 500:
        issue_id = IssueType.SERVER_ERROR
      elif res.status_code >= 400:
        issue_id = IssueType.CLIENT_ERROR
    except requests.exceptions.SSLError:
      issue_id = IssueType.INVALID_CERT
    except Exception:
      issue_id = IssueType.NO_SSL_SERVER
    return issue_id

  def __init__(self, creative_urls, protocol, phantomjs, browserjs, display_id, log_dir, cookie_dir, callback=None, debug=False):
    """
    Initialize the instance.

    :param creative_urls: a dictionary of a creative key and its url to be scanned.
    :param protocol: the server protocol, 'https' or 'http'.
    :param phantomjs: the path to the phantomjs command.
    :param browserjs: the path to the browser.js file.
    :param display_id: the number that represents the xvfb display id.
    :param log_dir: the directory into which the browser process saves the scan log.
    :param cookie_dir: the directory that contains cookies used by browsers while scanning.
    :param callback: the function called for passing the urls and issue ids found during this scanning process.
    :param debug: Turn on the debug mode, which temporarily to allow access to private network that host test creatives.
    """
    threading.Thread.__init__(self)
    self.creative_urls = creative_urls
    self.protocol = protocol
    self.phantomjs = phantomjs
    self.browserjs = browserjs
    self.display_id = display_id
    self.log_dir = log_dir
    self.cookie_dir = cookie_dir
    self.callback = callback
    self.debug = debug
    self.abort = False

  def _run_command(self, command):
    """
    Create a new process and execute the `command`.

    :param command: a list of strings that represents the command and command arguments.
    """
    print command
    process = subprocess.Popen(
      command, shell=False, env={'DISPLAY': ':%d' % self.display_id}, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    process.wait()
    print 'return: %d' % (process.wait(),)
    print 'stdout: %s' % (process.stdout.readlines(),)
    print 'stderr: %s' % (process.stderr.readlines(),)

  def _verify_each_url(self, creative_id, logfile):
    """
    Analyzes the browser's network log to check if https protocols are avaiable or not.

    :param creative_id: a list of creative ids.
    :param logfile: the path to the file in which the network log is saved.
    """
    if not os.path.exists(logfile):
      return

    data = None
    with open(logfile, 'r') as fp:
      data = json.load(fp)

    found = False

    session = requests.Session()
    session.max_redirects = 100
    if data:
      for key, value in data.iteritems():
        try:
          int(key)
        except ValueError:
          continue

        if data[key]['error'] and data[key]['error']['errorCode'] and data[key]['error']['errorCode'] == 999:
          issue_id = IssueType.PRIVATE_NETWORK
        else:
          url = data[key]['request']['url']
          issue_id = IssueType.NO_ISSUE
          if re.match(r'^https?:\/\/%s' % socket.gethostname(), url):
            continue
          elif re.match(r'^http', url):
            found = True
            issue_id = self.verify_http_url(session, url)
        if self.callback:
          self.callback(creative_id, issue_id, self.protocol, url=url)

    if not found and self.callback:
      self.callback(creative_id, IssueType.NO_EXTERNAL, self.protocol)

  def _create_command(self, url_obj, log_file):
    """
    Create a new process for a browser. The `url` will be viewed and the network log will be saved into `log_file`.

    :param url_obj: a dictionary of a url and a boolean flag indicating if the url is hosted locally or not.
    :param log_file: the path to the file to which network log is saved.
    :return: a string list of a command and its arguments.
    """
    command = []
    if self.display_id < 0:
      command.extend(['/usr/bin/xvfb-run', '--auto-servernum', '--server-args', '-screen 0 1024x768x24'])
    command.append(self.phantomjs)
    command.extend(['--web-security', 'false'])
    command.extend(['--load-plugins', 'true'])
    command.extend(['--ignore-ssl-errors', 'true'])
    command.extend(['--ssl-protocol', 'any'])  # Accept any ssl protocol, default only accepts SSLv3.
    command.append(self.browserjs)
    command.extend(['--use-cookie', 'true'])
    command.extend(['--enable-javascript', 'true'])
    command.extend(['--hosted-locally', url_obj['hosted_locally']])
    command.extend(['--url', url_obj['url']])
    command.extend(['--log-file', log_file])
    command.extend(['--debug', 'true' if self.debug else 'false'])
    if self.cookie_dir:
      command.extend(['--cookie-dir', self.cookie_dir])
    return command

  def run(self):
    """
    Start browsing the urls one by one.
    """
    try:
      for creative_id, url_obj in self.creative_urls.iteritems():
        if self.abort:
          break
        elif url_obj:
          log_file = '%s/%s.json' % (self.log_dir, creative_id)
          command = self._create_command(url_obj, log_file)
          self._run_command(command)
          self._verify_each_url(creative_id, log_file)
        elif self.callback:
          self.callback(creative_id, IssueType.NO_EXTERNAL, self.protocol)
    except:
      raise

  def shutdown(self):
    """
    Prevent the next scan to shutdown this browser.
    """
    self.abort = True


class BrowserController(object):
  """
  Class that allots creatives to BrowserHost instances.
  """

  @classmethod
  def create_html(cls, html, dest_file):
    """
    Create an html file and save it in `dest_file`.

    :param html: a string that contains html tags.
    :param dest_file: the path to file into which the html will be written.
    """
    with open(dest_file, 'w') as fp:
      fp.write(html.encode('utf-8'))

  def __init__(self, creatives, protocol, ports, browser_count, phantomjs, browserjs, cookie_dir, workspace, log_func, modify_func, debug=False, xserver_offset=1):
    """
    Initiate an instance.

    :param creatives: a list of creatives.
    :param protocol: a protocol, `https` or `http`.
    :param ports: a list of port numbers.
    :param browser_count: a number of browsers to be launched.
    :param phantomjs: the path to the phantomjs command.
    :param browserjs: the path to the browser.js file.
    :param cookie_dir: the directory that contains cookies, which will be used by browsers during scanning.
    :param workspace: the directory where the html files and scan logs are saved.
    :param log_func: the function called for passing the urls and issue ids found during this scanning process.
    :param modify_func: the function called for modifying the creatives.
    :param debug: Turn on the debug mode, which temporarily to allow access to private network that host test creatives.
    :param xserver_offset: an offset number, from which we will reserve IDs of X servers.
    """
    self.creatives = creatives
    self.protocol = protocol
    self.ports = ports
    self.browser_count = browser_count
    self.phantomjs = phantomjs
    self.browserjs = browserjs
    self.cookie_dir = cookie_dir
    self.workspace = workspace
    self.log_func = log_func
    self.modify_func = modify_func
    self.threads = []
    self.hostname = socket.gethostname()
    self.debug = debug
    self.xserver_offset = xserver_offset

  def _create_urls_to_scan(self, creatives, port):
    """
    Create urls to scan these creatives.

    :param creatives: a list of creatives.
    :param port: the port number used to scan these creatives.
    :return: a dictionary of a creative id and its url to be scanned.
    """
    url_dict = {}
    for creative in creatives:
      self.modify_func(creative)
      snippet = creative.modified_scan_snippet if self.protocol == 'https' else creative.scan_snippet

      if snippet:
        url_obj = None
        if re.match(r'^http', snippet, re.IGNORECASE):
          url_obj = {
            'url': snippet,
            'hosted_locally': 'false'
          }
        else:
          save_file = '%s/%s.html' % (self.workspace, creative.creative_id)
          self.create_html(snippet, save_file)
          url_obj = {
            'url': '%s://%s:%d/%s' % (self.protocol, self.hostname, port, save_file),
            'hosted_locally': 'true'
          }
        url_dict[str(creative.creative_id)] = url_obj
    return url_dict

  def start(self):
    """
    Start browsers.
    """
    # Caluculate how many creatives are allotted to each browser process.
    allotment = len(self.creatives) / self.browser_count
    if allotment == 0:
      allotment = 1
    if len(self.creatives) % allotment != 0:
      allotment += 1

    for i in xrange(0, self.browser_count):
      display_id = self.xserver_offset + i + 1
      log_dir = '%s/%d' % (self.workspace, i)

      allotted_creatives = self.creatives[(i * allotment):((i + 1) * allotment)]
      allotted_port = self.ports[i % len(self.ports)]

      url_dict = self._create_urls_to_scan(allotted_creatives, allotted_port)
      if len(url_dict) > 0:
        thread = BrowserHost(url_dict, self.protocol, self.phantomjs, self.browserjs, display_id, log_dir, self.cookie_dir, self.log_func, self.debug)
        thread.start()
        self.threads.append(thread)
        time.sleep(1)

  def wait(self):
    """
    Wait until all the threads done.
    """
    for thread in self.threads:
      if thread and thread.isAlive():
        thread.join()

  def shutdown(self):
    """
    Cloase all the browser threads.
    """
    for thread in self.threads:
      if thread and thread.isAlive():
        thread.shutdown()
