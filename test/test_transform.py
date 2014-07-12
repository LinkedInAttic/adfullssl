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

import unittest

import adscan.transform
from adscan.model import Creative


class TransformTestCase(unittest.TestCase):
  """
  Test the transform module.
  """

  @classmethod
  def create_to_dfp(cls, creative_type, sink, modified_snippet='<x>test</x>'):
    """
    Test the parameter in a DFP creative is used to store a modified snippet.
    """
    dfp_creative = {'Creative_Type': creative_type}
    creative = Creative(modified_snippet=modified_snippet)
    modified_dfp_creative = adscan.transform.to_dfp(creative, dfp_creative)
    assert modified_snippet == modified_dfp_creative[sink]

  @classmethod
  def create_from_dfp(
    self, creative_type, snippet_field, snippet_field2=None, snippet='<img src="http://example.com">',
    modified_snippet='<img src="//example.com">', expanded_snippet=None, modified_expanded_snippet=None):
    """
    Test the from_dfp method.
    """
    dfp_creative = {}
    dfp_creative['id'] = 11111
    dfp_creative['previewUrl'] = 'http://example.com'
    dfp_creative['Creative_Type'] = creative_type

    if snippet_field2:
      dfp_creative[snippet_field] = {}
      dfp_creative[snippet_field][snippet_field2] = snippet
    else:
      dfp_creative[snippet_field] = snippet

    if expanded_snippet:
      dfp_creative['expandedSnippet'] = expanded_snippet

    creative = adscan.transform.from_dfp(dfp_creative)

    assert creative.snippet == snippet
    assert creative.modified_snippet == modified_snippet
    if expanded_snippet:
      assert creative.expanded_snippet == expanded_snippet
    if modified_expanded_snippet:
      assert creative.modified_expanded_snippet == modified_expanded_snippet

  def test_renew(self):
    """
    Test to convert a creative from a cache.
    """
    cache = Creative(
      creative_id=1000, creative_type='DummyType', preview_url='DummyURL', snippet='<img src="http://example.com">')
    creative = adscan.transform.renew(cache)
    assert creative.creative_id == 1000
    assert creative.creative_type == 'DummyType'
    assert creative.preview_url == 'DummyURL'
    assert creative.snippet == '<img src="http://example.com">'
    assert creative.expanded_snippet is None
    assert creative.modified_snippet == '<img src="//example.com">'
    assert creative.modified_expanded_snippet is None

  def test_renew_third_party_creative(self):
    """
    Test to convert a third party creative, which has expanded snippet, to a cache.
    """
    cache = Creative(
      creative_id=1000, creative_type='ThirdPartyCreative', preview_url='DummyURL',
      snippet='<img src="http://example.com">',
      expanded_snippet='<img src="http://example.com"><img src="http://example.net">')
    creative = adscan.transform.renew(cache)
    assert creative.creative_id == 1000
    assert creative.creative_type == 'ThirdPartyCreative'
    assert creative.preview_url == 'DummyURL'
    assert creative.snippet == '<img src="http://example.com">'
    assert creative.expanded_snippet == '<img src="http://example.com"><img src="http://example.net">'
    assert creative.modified_snippet == '<img src="//example.com">'
    assert creative.modified_expanded_snippet == '<img src="//example.com"><img src="http://example.net">'

  def test_to_dfp_for_third_party_creative(self):
    """
    Test that a modified creative should inserted into snippet for ThirdPartyCreative.
    """
    self.create_to_dfp('ThirdPartyCreative', 'snippet')

  def test_to_dfp_for_ad_exchange_creative(self):
    """
    Test that a modified creative should inserted into codeSnippet for AdExchangeCreative.
    """
    self.create_to_dfp('AdExchangeCreative', 'codeSnippet')

  def test_to_dfp_for_ad_sense_creative(self):
    """
    Test that a modified creative should inserted into codeSnippet for AdSenseCreative.
    """
    self.create_to_dfp('AdSenseCreative', 'codeSnippet')

  def test_to_dfp_for_custom_creative(self):
    """
    Test that a modified creative should inserted into htmlSnippet for CustomCreative.
    """
    self.create_to_dfp('CustomCreative', 'htmlSnippet')

  def test_to_dfp_for_flash_creative(self):
    """
    Test that a modified creative should inserted into flashName for FlashCreative.
    """
    self.create_to_dfp('FlashCreative', 'flashName')

  def test_to_dfp_for_internal_redirect_creative(self):
    """
    Test that a modified creative should inserted into internalRedirectUrl for InternalRedirectCreative.
    """
    self.create_to_dfp('InternalRedirectCreative', 'internalRedirectUrl')

  def test_to_dfp_for_image_creative(self):
    """
    Test that a modified creative should inserted into primaryImageAsset.assetUrl for ImageCreative.
    """
    dfp_creative = {
      'Creative_Type': 'ImageCreative',
      'primaryImageAsset': {}
    }
    modified_snippet = '<x>test</x>'
    creative = Creative(modified_snippet=modified_snippet)
    modified_dfp_creative = adscan.transform.to_dfp(creative, dfp_creative)
    assert modified_snippet == modified_dfp_creative['primaryImageAsset']['assetUrl']

  def test_to_dfp_for_image_redirect_creative(self):
    """
    Test that a modified creative should inserted into imageUrl for ImageRedirectCreative.
    """
    self.create_to_dfp('ImageRedirectCreative', 'imageUrl')

  def test_to_dfp_for_image_redirect_overlay_creative(self):
    """
    Test that a modified creative should inserted into imageUrl for ImageRedirectOverlayCreative.
    """
    self.create_to_dfp('ImageRedirectOverlayCreative', 'imageUrl')

  def test_to_dfp_for_vast_redirect_creative(self):
    """
    Test that a modified creative should inserted into vastXmlUrl for VastRedirectCreative.
    """
    self.create_to_dfp('VastRedirectCreative', 'vastXmlUrl')

  def test_to_dfp_for_aspect_ratio_image_creative(self):
    """
    Test that a modified creative should inserted into thirdPartyImpressionUrl for AspectRatioImageCreative.
    """
    self.create_to_dfp('AspectRatioImageCreative', 'thirdPartyImpressionUrl')

  def test_to_dfp_for_template_creative(self):
    """
    Test that a modified creative should inserted into a value of creativeTemplateVariableValues parameter for TemplateCreative.
    """
    dfp_creative = {
      'Creative_Type': 'TemplateCreative',
      'creativeTemplateVariableValues': [{'value': 'http://www.example.com/ads'}]
    }
    modified_snippet = '<img src="https://www.example.com/ads">'
    creative = Creative(modified_snippet=modified_snippet)
    modified_dfp_creative = adscan.transform.to_dfp(creative, dfp_creative)
    assert 'https://www.example.com/ads' == modified_dfp_creative['creativeTemplateVariableValues'][0]['value']

  def test_to_dfp_for_template_creative_with_unmodified_url(self):
    """
    Test that a modified creative should inserted into a value of creativeTemplateVariableValues parameter for TemplateCreative.
    """
    dfp_creative = {
      'Creative_Type': 'TemplateCreative',
      'creativeTemplateVariableValues': [{'value': 'http://www.example.com/ads'}, {'value': 'http://www.example.net/ads'}]
    }
    creative = Creative(modified_snippet='<img src="https://www.example.com/ads">')
    modified_dfp_creative = adscan.transform.to_dfp(creative, dfp_creative)
    assert 'https://www.example.com/ads' == modified_dfp_creative['creativeTemplateVariableValues'][0]['value']
    assert 'http://www.example.net/ads' == modified_dfp_creative['creativeTemplateVariableValues'][1]['value']

  def test_from_dfp_adexchange_creative(self):
    """
    Test to convert a DFP AdExchangeCreative to a creative.
    """
    self.create_from_dfp('AdExchangeCreative', 'codeSnippet')

  def test_from_dfp_adsense_creative(self):
    """
    Test to convert a DFP AdSenseCreative to a creative.
    """
    self.create_from_dfp('AdSenseCreative', 'codeSnippet')

  def test_from_dfp_custom_creative(self):
    """
    Test to convert a DFP CustomCreative to a creative.
    """
    self.create_from_dfp('CustomCreative', 'htmlSnippet')

  def test_from_dfp_flash_creative(self):
    """
    Test to convert a DFP FlashCreative to a creative.

    Pass this test because no modification is made to this creative.
    """
    pass

  def test_from_dfp_image_creative(self):
    """
    Test to convert a DFP ImageCreative to a creative.
    """
    self.create_from_dfp('ImageCreative', 'primaryImageAsset', snippet_field2='assetUrl')

  def test_from_dfp_internal_redirect_creative(self):
    """
    Test to convert a DFP InternalRedirectCreative to a creative.
    """
    self.create_from_dfp('InternalRedirectCreative', 'internalRedirectUrl')

  def test_from_dfp_image_redirect_creative(self):
    """
    Test to convert a DFP ImageRedirectCreative to a creative.
    """
    self.create_from_dfp('ImageRedirectCreative', 'imageUrl')

  def test_from_dfp_image_redirect_overlay_creative(self):
    """
    Test to convert a DFP ImageRedirectOverlayCreative to a creative.
    """
    self.create_from_dfp('ImageRedirectOverlayCreative', 'imageUrl')

  def test_from_dfp_vast_redirect_creative(self):
    """
    Test to convert a DFP VastRedirectCreative to a creative.
    """
    self.create_from_dfp('VastRedirectCreative', 'vastXmlUrl')

  def test_from_dfp_aspect_ratio_image_creative(self):
    """
    Test to convert a DFP AspectRatioImageCreative to a creative.
    """
    self.create_from_dfp('AspectRatioImageCreative', 'thirdPartyImpressionUrl')

  def test_from_dfp_template_creative(self):
    """
    Test to convert a DFP TemplateCreative to a creative.

    Not test this creative because a url to a real web page is required.
    """
    pass

  def test_from_dfp_third_party_creative(self):
    """
    Test to convert a DFP ThirdPartyCreative to a creative.
    """
    self.create_from_dfp(
      'ThirdPartyCreative', 'snippet', expanded_snippet='<img src="http://example.com">',
      modified_expanded_snippet='<img src="//example.com">')

  def test_modify_snippet_iframe(self):
    """
    Test to modify the http protocol into a relative protocol.
    """
    snippet = "<iframe src='http://www.example.com/ads'></iframe>"
    expect = "<iframe src='//www.example.com/ads'></iframe>"
    actual = adscan.transform.modify_snippet(snippet)
    assert expect == actual, 'Expected\n%s\n\nBut was\n%s' % (expect, actual)

  def test_modify_snippet_img(self):
    """
    Test to modify the http protocol into a relative protocol even when the protocol uses captal letters.
    """
    snippet = "<img src='HTTP://www.example.com/ads'/>"
    expect = "<img src='//www.example.com/ads'/>"
    actual = adscan.transform.modify_snippet(snippet)
    assert expect == actual, 'Expected\n%s\n\nBut was\n%s' % (expect, actual)

  def test_modify_snippet_ignore_case(self):
    """
    Test to modify the http protocol with ignore case.
    """
    snippet = "<IMG SRC='HTTP://www.example.com/ads'/>"
    expect = "<IMG SRC='//www.example.com/ads'/>"
    actual = adscan.transform.modify_snippet(snippet)
    assert expect == actual, 'Expected\n%s\n\nBut was\n%s' % (expect, actual)

  def test_modify_snippet_link_rel(self):
    """
    Test to modify the http protocol in styesheets.
    """
    snippet = "<link rel=stylesheet type=text/css href=http://www.example.com/ads>"
    expect = "<link rel=stylesheet type=text/css href=//www.example.com/ads>"
    actual = adscan.transform.modify_snippet(snippet)
    assert expect == actual, 'Expected\n%s\n\nBut was\n%s' % (expect, actual)

  def test_modify_snippet_link_rel_different_order(self):
    """
    Test to modify the http protocol in styesheets.
    """
    snippet = "<link type=text/css href=http://www.example.com/ads rel=stylesheet >"
    expect = "<link type=text/css href=//www.example.com/ads rel=stylesheet >"
    actual = adscan.transform.modify_snippet(snippet)
    assert expect == actual, 'Expected\n%s\n\nBut was\n%s' % (expect, actual)

  def test_modify_snippet_script_content(self):
    """
    Test to modify the http protocol in a script src.
    """
    snippet = "<script language='JavaScript' type='text/javascript'>var src = 'http://www.example.com/ads';</script>"
    expect = "<script language='JavaScript' type='text/javascript'>var src = '//www.example.com/ads';</script>"
    actual = adscan.transform.modify_snippet(snippet)
    assert expect == actual, 'Expected\n%s\n\nBut was\n%s' % (expect, actual)

  def test_modify_snippet_script_content_ignore_case(self):
    """
    Test to modify the http protocol in a script src with ignore case.
    """
    snippet = "<script language='JavaScript' type='text/javascript'>var src = 'HTTP://www.example.com/ads';</script>"
    expect = "<script language='JavaScript' type='text/javascript'>var src = '//www.example.com/ads';</script>"
    actual = adscan.transform.modify_snippet(snippet)
    assert expect == actual, 'Expected\n%s\n\nBut was\n%s' % (expect, actual)

  def test_modify_snippet_script_content_img(self):
    """
    Test to modify the http protocol inside of a script tag.
    """
    snippet = "<script language='JavaScript' type='text/javascript'>document.write(<img src='http://www.example.com/ads'>"
    expect = "<script language='JavaScript' type='text/javascript'>document.write(<img src='//www.example.com/ads'>"
    actual = adscan.transform.modify_snippet(snippet)
    assert expect == actual, 'Expected\n%s\n\nBut was\n%s' % (expect, actual)

  def test_modify_snippet_script_content_img_ignore_case(self):
    """
    Test to modify the http protocol inside of a script tag with ignore case.
    """
    snippet = "<script language='JavaScript' type='text/javascript'>document.write(<IMG SRC='HTTP://www.example.com/ads'>"
    expect = "<script language='JavaScript' type='text/javascript'>document.write(<IMG SRC='//www.example.com/ads'>"
    actual = adscan.transform.modify_snippet(snippet)
    assert expect == actual, 'Expected\n%s\n\nBut was\n%s' % (expect, actual)

  def test_modify_snippet_script_content_img_multiple_attrs(self):
    """
    Test to modify multiple http protocols inside of a script tag.
    """
    snippet = "<script language='JavaScript' type='text/javascript'>document.write(<img x=1 y=z src='http://www.example.com/ads' z=12></script>"
    expect = "<script language='JavaScript' type='text/javascript'>document.write(<img x=1 y=z src='//www.example.com/ads' z=12></script>"
    actual = adscan.transform.modify_snippet(snippet)
    assert expect == actual, 'Expected\n%s\n\nBut was\n%s' % (expect, actual)

  def test_modify_snippet_ignore_href_in_script_content(self):
    """
    Test to ignore anchor href inside of a script tag.
    """
    snippet = "<script language=JavaScript type=text/javascript>document.write('<a href=http://www.example.com/ads>x</a>');</script>"
    expect = "<script language=JavaScript type=text/javascript>document.write('<a href=http://www.example.com/ads>x</a>');</script>"
    actual = adscan.transform.modify_snippet(snippet)
    assert expect == actual, 'Expected\n%s\n\nBut was\n%s' % (expect, actual)

  def test_modify_snippet_ignore_href_in_script_content_multiple_attrs(self):
    """
    Test to ignore anchor href inside of a script tag with multiple attributes.
    """
    snippet = "<script language=JavaScript type=text/javascript>document.write('<a x=1 y=z  href=http://www.example.com/ads z=12>x</a>');</script>"
    expect = "<script language=JavaScript type=text/javascript>document.write('<a x=1 y=z  href=http://www.example.com/ads z=12>x</a>');</script>"
    actual = adscan.transform.modify_snippet(snippet)
    assert expect == actual, 'Expected\n%s\n\nBut was\n%s' % (expect, actual)

  def test_modify_snippet_ignore_percent_c(self):
    """
    Test to ignore urls starting with %c, which will be automatically replaced with the proper protocl at DFP.
    """
    snippet = "<iframe src='%chttp://www.example.com/ads'></iframe>"
    expect = "<iframe src='%chttp://www.example.com/ads'></iframe>"
    actual = adscan.transform.modify_snippet(snippet)
    assert expect == actual, 'Expected\n%s\n\nBut was\n%s' % (expect, actual)

  def test_modify_snippet_script_comment(self):
    """
    Test to modify urls inside of a script tag..
    """
    snippet = '<script><!-- var a = "http://www.example.com/ads"; --></script>'
    expect = '<script><!-- var a = "//www.example.com/ads"; --></script>'
    actual = adscan.transform.modify_snippet(snippet)
    assert expect == actual, 'Expected\n%s\n\nBut was\n%s' % (expect, actual)

  def test_modify_snippet_script_multiple(self):
    """
    Test to modify multiple urls inside of a scipt tag.
    """
    snippet = '<script><!-- var a = "http://www.example.com/ads"; var b = "http://www.example.com/ads"; --></script>'
    expect = '<script><!-- var a = "//www.example.com/ads"; var b = "//www.example.com/ads"; --></script>'
    actual = adscan.transform.modify_snippet(snippet)
    assert expect == actual, 'Expected\n%s\n\nBut was\n%s' % (expect, actual)

  def test_modify_snippet_script_multiple_multiline(self):
    """
    Test to modify multiple urls inside of a multiline comment.
    """
    snippet = """<script><!--
        var a = "http://www.example.com/ads";
        var b = "http://www.example.com/ads";
      --></script>"""
    expect = """<script><!--
        var a = "//www.example.com/ads";
        var b = "//www.example.com/ads";
      --></script>"""
    actual = adscan.transform.modify_snippet(snippet)
    assert expect == actual, 'Expected\n%s\n\nBut was\n%s' % (expect, actual)

  def test_modify_snippet_script_math(self):
    """
    Test to modify urls even when a smaller/greater-than sign is used inside of a script tag.
    """
    snippet = '<script><!-- if(x<z){var a = "http://www.example.com/ads"}; --></script>'
    expect = '<script><!-- if(x<z){var a = "//www.example.com/ads"}; --></script>'
    actual = adscan.transform.modify_snippet(snippet)
    assert expect == actual, 'Expected\n%s\n\nBut was\n%s' % (expect, actual)

  def test_modify_snippet_script_protocols(self):
    """
    Test to ignore protocols that does not have hosts.
    """
    snippet = '<script>var cspJsHost = (("https:" == document.location.protocol) ? "https://" : "http://");</script>'
    expect = snippet
    actual = adscan.transform.modify_snippet(snippet)
    assert expect == actual, 'Expected\n%s\n\nBut was\n%s' % (expect, actual)

  def test_modify_snippet_script_with_base_snippet(self):
    """
    Test to ignore urls that does not appear in the base snippet. A base_snippet is used in ThirdPartyCreative.
    """
    snippet = "<script>screenad = {clicks: ['http://www.example.com/ads']};</script>"
    base_snippet = "<script>screenad = {clicks: ['%%CLICK_URL_UNESC%%//www.example.com/ads']};</script>"
    expect = snippet
    actual = adscan.transform.modify_snippet(snippet, base_snippet=base_snippet)
    assert expect == actual, 'Expected\n%s\n\nBut was\n%s' % (expect, actual)

  def test_modify_snippet_with_base_values(self):
    """
    Test to modify only urls that appear in the base snippet.
    """
    snippet = '<a href="http://www.example.net">a</a><img src="http://www.example.com/ads"><script>document.write(\'<img src="http://www.example.net/ads">\')</script>'
    expect = '<a href="http://www.example.net">a</a><img src="https://www.example.com/ads"><script>document.write(\'<img src="http://www.example.net/ads">\')</script>'
    base_values = [
      {'uniqueName': 'x', 'value': 'y', 'BaseCreativeTemplateVariableValue_Type': 'StringCreativeTemplateVariableValue'},
      {'uniqueName': 'z', 'value': 'http://www.example.com/ads', 'BaseCreativeTemplateVariableValue_Type': 'UrlCreativeTemplateVariableValue'}
    ]
    actual = adscan.transform.modify_snippet(snippet, base_values=base_values)
    assert expect == actual, 'Expected\n%s\n\nBut was\n%s' % (expect, actual)

  def test_replace_percent_h_content(self):
    """
    Test to replace the %h with url.
    """
    snippet = '<a href="%c%u" target="_top"><img src="%h/ads" border="0"></a>'
    preview_html = '<a href="https://www.example.com/" target="_top"><img src="https://www.example.com/ads" border="0"></a>'
    expect = '<a href="%c%u" target="_top"><img src="https://www.example.com/ads" border="0"></a>'
    actual = adscan.transform.replace_percent_h(snippet, html=preview_html)
    assert expect == actual, 'Expected\n%s\n\nBut was\n%s' % (expect, actual)

  def test_replace_percent_h_content_multiple(self):
    """
    Test to replace the multiple %h with urls.
    """
    snippet = '<a href="%c%u" target="_top"><img src="%h/ads1" border="0">%h/ads2</a>'
    preview_html = '<a href="https://www.example.com" target="_top"><img src="https://www.example.com/ads1" border="0">http://www.example.com/ads2</a>'
    expect = '<a href="%c%u" target="_top"><img src="https://www.example.com/ads1" border="0">https://www.example.com/ads2</a>'
    actual = adscan.transform.replace_percent_h(snippet, html=preview_html)
    assert expect == actual, 'Expected\n%s\n\nBut was\n%s' % (expect, actual)

  def test_replace_percent_h(self):
    """
    Test to replace the %h with url.
    """
    snippet = '<a href="%c%u" target="_top"><img src="%h/ads" border="0"></a>'
    preview_html = '<a href="http://www.example.com" target="_top"><img src="https://www.example.com/ads" border="0"></a>'
    expect = '<a href="%c%u" target="_top"><img src="https://www.example.com/ads" border="0"></a>'
    actual = adscan.transform.replace_percent_h(snippet, html=preview_html)
    assert expect == actual, 'Expected\n%s\n\nBut was\n%s' % (expect, actual)

  def test_replace_percent_h_no_change(self):
    """
    Test to not replace the %http://.
    """
    snippet = '<img src="%https://www.example.com">'
    preview_html = '<img src="https://www.example.com">'
    expect = '<img src="%https://www.example.com">'
    actual = adscan.transform.replace_percent_h(snippet, html=preview_html)
    assert expect == actual, 'Expected\n%s\n\nBut was\n%s' % (expect, actual)
