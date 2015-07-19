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
Utility functions that transform a creative from/to another object.
"""

import re
import lxml
import lxml.etree
import lxml.html
import lxml.cssselect
import requests

import googleads.dfp

from adscan.model import Creative


def to_dfp(creative, dfp_creative, debug=False):
  """
  Convert an instance of :class:`~model.Creative` into an object used in DFP.

  :param creative: an instance of :class:`~model.Creative`.
  :param dfp_creative: a creative object downloaded from DFP.
  :return: the modified DFP creative. If not supported, None will be returned.
  """
  m_snippet = creative.modified_snippet
  dfp = dfp_creative
  ctype = dfp['xsi_type'] if debug else googleads.dfp.DfpClassType(dfp_creative)

  if ctype == 'ThirdPartyCreative':
    dfp['snippet'] = m_snippet
  elif ctype in ['AdExchangeCreative', 'AdSenseCreative']:
    dfp['codeSnippet'] = m_snippet
  elif ctype == 'CustomCreative':
    dfp['htmlSnippet'] = m_snippet
  elif ctype == 'FlashCreative':
    dfp['flashName'] = m_snippet
  elif ctype == 'ImageCreative':
    dfp['primaryImageAsset']['assetUrl'] = m_snippet
  elif ctype == 'InternalRedirectCreative':
    dfp['internalRedirectUrl'] = m_snippet
  elif ctype in ['ImageRedirectCreative', 'ImageRedirectOverlayCreative']:
    dfp['imageUrl'] = m_snippet
  elif ctype == 'VastRedirectCreative':
    dfp['vastXmlUrl'] = m_snippet
  elif ctype == 'AspectRatioImageCreative':
    dfp['thirdPartyImpressionUrl'] = m_snippet
  elif ctype == 'TemplateCreative':
    if 'creativeTemplateVariableValues' in dfp:
      for v in dfp['creativeTemplateVariableValues']:
        if v.__class__.__name__ == 'StringCreativeTemplateVariable' or debug:
          regex_url = re.compile(r'^http\:((\/\/[^\/]*).*)$', re.IGNORECASE)
          match = regex_url.match(v.defaultValue)
          if match:
            url = match.group(1)
            host = match.group(2)
            regex_secure_url = r'(\'|\")(https\:)?' + re.escape(host)
            if re.search(regex_secure_url, m_snippet, re.IGNORECASE):
              v.defaultValue = 'https:' + url
  else:
    # not supported
    dfp = None
  return dfp


def from_dfp(dfp_creative, debug=False):
  """
  Convert a creative object downloaded from DFP into an instance of
  :class:`~model.Creative`.

  :param dfp_creative: a creative object downloaded from DFP.
  :return: an instance of :class:`~model.Creative`.
  """
  if not dfp_creative or 'previewUrl' not in dfp_creative:
    return

  dfp = dfp_creative
  creative_id = dfp['id']
  creative_type = dfp['xsi_type'] if debug else googleads.dfp.DfpClassType(dfp_creative)
  preview_url = dfp['previewUrl']
  modified = False
  snippet = None
  m_snippet = None  # Modified snippet.
  e_snippet = None  # Expanded snippet.
  me_snippet = None  # Modified expanded snippet.

  if creative_type == 'ThirdPartyCreative':
    snippet, m_snippet = get_snippet(dfp['snippet'])
    e_snippet, me_snippet = get_snippet(dfp['expandedSnippet'], base_snippet=snippet)
  elif creative_type in ['AdExchangeCreative', 'AdSenseCreative']:
    snippet, m_snippet = get_snippet(dfp['codeSnippet'])
  elif creative_type == 'CustomCreative':
    snippet, m_snippet = get_snippet(dfp['htmlSnippet'])
  elif creative_type == 'FlashCreative':
    snippet = download_html(re.sub(r'^http\:', r'https:', preview_url))
    m_snippet = snippet
  elif creative_type == 'ImageCreative':
    snippet, m_snippet = get_snippet(dfp['primaryImageAsset']['assetUrl'])
  elif creative_type == 'InternalRedirectCreative':
    snippet, m_snippet = get_snippet(dfp['internalRedirectUrl'])
  elif creative_type in ['ImageRedirectCreative', 'ImageRedirectOverlayCreative']:
    snippet, m_snippet = get_snippet(dfp['imageUrl'])
  elif creative_type == 'VastRedirectCreative':
    snippet, m_snippet = get_snippet(dfp['vastXmlUrl'])
  elif creative_type == 'AspectRatioImageCreative':
    snippet, m_snippet = get_snippet(dfp['thirdPartyImpressionUrl'])
  elif creative_type == 'TemplateCreative':
    snippet = download_html(re.sub(r'^http\:', r'https:', preview_url))
    base_values = []
    if 'creativeTemplateVariableValues' in dfp:
      # Only StringCreativeTemplateVariable can contain string values; meaning url can be stored.
      base_values = [v for v in dfp['creativeTemplateVariableValues'] if v.__class__.__name__ == 'StringCreativeTemplateVariable']
    m_snippet = modify_snippet(snippet, base_values=base_values)

  if snippet:
    if snippet == m_snippet:
      m_snippet = None
    else:
      modified = True

  if e_snippet:
    if e_snippet == me_snippet:
      me_snippet = None
    else:
      modified = True

  if snippet and type(snippet) != unicode:
    snippet = snippet.decode('utf-8')
  if m_snippet and type(m_snippet) != unicode:
    m_snippet = m_snippet.decode('utf-8')
  if e_snippet and type(e_snippet) != unicode:
    e_snippet = e_snippet.decode('utf-8')
  if me_snippet and type(me_snippet) != unicode:
    me_snippet = me_snippet.decode('utf-8')

  return Creative(
    creative_id=creative_id, creative_type=creative_type, preview_url=preview_url, modified=modified, snippet=snippet,
    modified_snippet=m_snippet, expanded_snippet=e_snippet, modified_expanded_snippet=me_snippet)


def renew(creative):
  """
  Create a new instance of :class:`~model.Creative` from the specified `creative`.
  The `created_at`, `modified`, `modified_snippet`, and `modified_expanded_snippet` will be updated.

  :param creative: an instance of :class:`~model.Creative`.
  :return: a new instance of :class:`~model.Creative`.
  """
  modified = False
  snippet = creative.snippet
  e_snippet = creative.expanded_snippet
  m_snippet = None
  me_snippet = None

  if creative.creative_type == 'ThirdPartyCreative':
    m_snippet = modify_snippet(snippet)
    me_snippet = modify_snippet(e_snippet, base_snippet=snippet)
  else:
    snippet, m_snippet = get_snippet(snippet)

  if snippet:
    if snippet == m_snippet or not m_snippet:
      m_snippet = None
    else:
      modified = True
  if e_snippet:
    if e_snippet == me_snippet or not me_snippet:
      me_snippet = None
    else:
      modified = True

  return Creative(
    creative_id=creative.creative_id, creative_type=creative.creative_type, preview_url=creative.preview_url, modified=modified,
    snippet=snippet, modified_snippet=m_snippet, expanded_snippet=e_snippet, modified_expanded_snippet=me_snippet)


def get_snippet(snippet, base_snippet=None):
  """
  Create a modified snippets by investigating the snippet.

  :param snippet: a string that represents a snippet, or an ad html tag.
  :param base_snippet: an editable snippet, which is only used when `snippet` is not editable.
  :return: a pair of snippet and modified snippet.
  """
  # Workaround for a bug in suds.sax.text.Text https://bugs.launchpad.net/ubuntu/+source/suds/+bug/1100758
  if snippet.__class__.__module__ == "suds.sax.text" and snippet.__class__.__name__ == "Text":
    snippet = snippet.__repr__()

  regex_http = re.compile(r'^http', re.IGNORECASE)
  regex_url = re.compile(r'^http\:\/\/([\w\-\.\@\:]+)', re.IGNORECASE | re.MULTILINE)

  m_snippet = None
  if regex_http.match(snippet):
    m_snippet = regex_url.sub(r'https://\1', snippet)
  else:
    m_snippet = modify_snippet(snippet, base_snippet=base_snippet)
  return (snippet, m_snippet)


def modify_snippet(snippet, base_snippet=None, base_values=None):
  """
  Create a modified snippet.

  :param snippet: a string that represents a snippet, or an ad html tag.
  :param base_snippet: an editable snippet, which is used only when `snippet` is not editable.
  :param base_values: a dictionary, which is used only when the editable strings in `snippet` should appear in the
    dictionary values.
  :return: a string that represents a modified snippet.
  """
  attrs = [
    ('*[src]', 'src'),
    ('*[background]', 'background'),
    ('link[href][rel=stylesheet]', 'href'),
    ('object[data]', 'data'),
    ('applet[code]', 'code')
  ]
  elem_bodies = ['script', 'style']

  m_snippet = snippet

  try:
    doc = lxml.html.fromstring(m_snippet)
    for selector, attr in attrs:
      for node in doc.cssselect(selector):
        url = node.get(attr)
        m_snippet = modify_snippet_for_attr(m_snippet, url, base_snippet=base_snippet, base_values=base_values)
    for selector in elem_bodies:
      for node in doc.cssselect(selector):
        content = node.text_content()
        m_snippet = modify_snippet_for_elembody(m_snippet, content, base_snippet=base_snippet, base_values=base_values)
  except lxml.etree.XMLSyntaxError:
    pass
  except lxml.etree.ParserError:
    pass
  except:
    raise
  return m_snippet


def modify_snippet_for_attr(snippet, url, base_snippet=None, base_values=None):
  """
  Create a modified snippet for the urls in html attributes.

  :param snippet: a string that represents a snippet, or an ad html tag.
  :param url: a url.
  :param base_snippet: an editable snippet, which is used only when `snippet` is not editable.
  :param base_values: a dictionary, which is used only when the editable strings in `snippet` should appear in the
    dictionary values.
  :return: a string that represents a modified snippet.
  """
  match = re.match(r'^http:(//([^\/]*).*)$', url, re.IGNORECASE)
  if match:
    replacement = match.group(1)
    host = match.group(2)

    in_snippet = exist_in_snippet(host, base_snippet)
    in_values = exist_in_string_creative_template_variables(host, base_values)

    if in_values:
      replacement = 'https:%s' % replacement

    if ((not base_snippet) or in_snippet) and ((not base_values) or in_values):
      return re.sub(re.escape(url), replacement, snippet, re.IGNORECASE | re.MULTILINE)
  return snippet


def modify_snippet_for_elembody(snippet, content, base_snippet=None, base_values=None):
  """
  Create a modified snippet for the urls in html element body.

  :param snippet: a string that represents a snippet, or an ad html tag.
  :param content: a string in an html element body.
  :param base_snippet: an editable snippet, which is used only when `snippet` is not editable.
  :param base_values: a dictionary, which is used only when the editable strings in `snippet` should appear in the
    dictionary values.
  :return: a string that represents a modified snippet.
  """
  # This regex matches the URLs that are not prefixed with a pecent sign and an
  # alphabet.
  regex_for_url_without_percent = re.compile(r"""
    (?<!\%[a-z])  # No percent sign and an alphabet.
    (http\:
      (\/\/
        ([^\/\'\"\?\#]+)  # Host and port.
      [^\s\'\"\<\>]+)  # Rest of URL.
    )
  """, re.IGNORECASE | re.MULTILINE | re.VERBOSE)

  # This regex matches the string
  regex_for_tags_in_js = r"""
    \<  # The beginning of a tag.
    (?P<TAG>[a-zA-Z][\w\-]*)  # Tag name.
    (?:\s+
      (?:[\w\-]+\=[^\s\<\>]+)*
    )*  # Attribute.
    (?P<ATTR>[\w\-]+)  # Attribute name.
    \=[\s\'\"]?%s[^\>]*\>  # Value the contains a string specified into '%%s'.
  """

  regex_src_bg = re.compile(r'src|background', re.IGNORECASE)
  regex_link = re.compile(r'link', re.IGNORECASE)
  regex_href = re.compile(r'href', re.IGNORECASE)

  m_snippet = snippet
  matches = regex_for_url_without_percent.findall(content)
  for match in matches:
    original_url = match[0]
    replacement = match[1]
    host = match[2]
    modify = False

    # Skip if document.write('<a href=url>') but be careful; we need to find document.write(<img src=url>)
    regex = re.compile(regex_for_tags_in_js % re.escape(original_url), re.MULTILINE | re.VERBOSE)
    appearance = regex.search(content)
    if appearance:
      inner_tag = appearance.group('TAG')
      inner_attr = appearance.group('ATTR')
      if regex_src_bg.match(inner_attr) or (regex_link.match(inner_tag) and regex_href.match(inner_attr)):
        modify = True
    else:
      modify = True

    in_snippet = exist_in_snippet(host, base_snippet)
    in_values = exist_in_string_creative_template_variables(host, base_values)

    if in_values:
      replacement = 'https:%s' % replacement

    if modify and ((not base_snippet) or in_snippet) and ((not base_values) or in_values):
      escaped = re.escape(original_url)
      m_snippet = re.sub(escaped, replacement, m_snippet, re.MULTILINE)
  return m_snippet


def replace_percent_h(snippet, preview_url=None, html=None):
  """
  Replace %%h in the snippet with an actual domain.

  :param snippet: a string that represents a snippet, or an ad html tag.
  :param preview_url: the url to fetch the html code. It is used when `html` arg is not set.
  :param html: the actual html code.
  :return: a snippet in which %%h is replaced with an actual domain.
  """
  # Regex for finding %h.
  regex_percent_h = re.compile(r'%h(?!ttp)', re.MULTILINE)

  # Regex for finding strings next to %h.
  regex_adjacent = re.compile(r'\%h(?!ttp)([^\s\'\"\<\>]+)', re.MULTILINE)

  # Regex for finding hosts.
  regex_host = re.compile(r'^http\:\/\/([\w\-\.\@\:]+)', re.IGNORECASE | re.MULTILINE)

  # Regex for finding urls specified in %s.
  regex_url = r'((?:https?\:)?\/\/[^\s\'\"\<\>]+%s)'

  if snippet and regex_percent_h.search(snippet):
    if not html:
      html = download_html(preview_url)
    replaced_snippet = snippet

    match_h = regex_adjacent.search(replaced_snippet)
    while match_h:
      path = match_h.group(1)

      # Look for urls that has the specified `path` from the html. If found, replace the %h with the finding. Otherwise,
      # replace the %h with the doubleclick url.
      match_url = re.search(regex_url % re.escape(path), html, re.MULTILINE)
      replace_url = regex_host.sub(r'https://\1', match_url.group(1) if match_url else 'https://ad.doubleclick.net%s' % path)

      # Replace `%h/path` with the replace_url.
      keyword = r'%%h%s' % re.escape(path)
      replaced_snippet = re.sub(keyword, replace_url, replaced_snippet)

      match_h = regex_adjacent.search(replaced_snippet)
    return replaced_snippet
  else:
    return snippet


def exist_in_snippet(host, snippet):
  """
  Check if the host name appears in the snippet.

  :param host: a host name.
  :param snippet: a string that indicates a snippet, or an ad html tag.
  :return: a boolean that indicates whether the host name exists in the snippet.
  """
  regex = re.compile(re.escape(r'http://%s' % host), re.IGNORECASE)
  return snippet and regex.search(snippet)


def exist_in_string_creative_template_variables(host, variables):
  """
  Check if the host name appears in any of instances of StringCreativeTemplateVariable.

  :param host: a host name.
  :param variables: a list of instances of StringCreativeTemplateVariable.
  :return: a boolean that indicates whether the `host` exists in the `variables`.
  """
  if variables:
    regex = re.compile(re.escape(r'http://%s' % host), re.IGNORECASE)
    for v in variables:
      if regex.match(v.defaultValue):
        return True
  return False


def create_scan_snippet(creative):
  """
  Create a snippet used to be browsed.
  """
  snippet = creative.snippet
  e_snippet = creative.expanded_snippet
  s_snippet = e_snippet if e_snippet else snippet
  s_snippet = replace_percent_h(s_snippet, preview_url=creative.preview_url)

  ms_snippet = None
  if creative.modified_expanded_snippet:
    ms_snippet = creative.modified_expanded_snippet
  elif e_snippet:
    ms_snippet = e_snippet
  elif creative.modified_snippet:
    ms_snippet = creative.modified_snippet
  else:
    ms_snippet = snippet
  ms_snippet = replace_percent_h(ms_snippet, preview_url=creative.preview_url)

  creative.scan_snippet = s_snippet
  creative.modified_scan_snippet = ms_snippet


def download_html(url):
  """
  Download the html code from the url.

  :param url: the url.
  :return: the downloaded html.
  """
  r = requests.get(url, verify=False)
  return r.text

