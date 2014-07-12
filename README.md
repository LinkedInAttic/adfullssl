# AdFullSsl

AdFullSsl is a tool that can automatically detect SSL non-compliant ads and fix them.

## Background

Web browsers connect HTTPS pages using encrypted connection with SSL/TLS, but no encryption is made on regular HTTP connections. If the HTTPS page includes contents retrieved through HTTP (insecure) connections, the user is subject to a risk of main-in-the-middle attack, in which an attacker can steal user's sensitive information on unencrypted connection.

As a practical countermeasure, insecure contents are blocked by default on HTTPS pages on recent versions of web browsers after Firefox 23, Chrome 21 and Internet Explorer 10. However, it will break page layout and some functionalities. Internet Explorer displays an annoying warning message each time insecure content is detected. To prevent such poor user experience, all contents should be served over HTTPS on HTTPS pages.

Ads are not exceptions. Many web pages contain ads and these ads often use external resources, such as iframes, flash files, images, and stylesheets.

## Overview

The goal of AdFullSsl is to detect SSL non-compliant ads and fix them. To this end, it mainly performs the following steps:

1. Modify ads by replacing http: with https: or relative protocol in which URLs does not have protocol
2. Locate ads on HTTPS server and browse them with headless browsers to capture all the traffic
3. Analyze the traffic to detect insecure requests
4. Upload the modified ads if any modification was made on step 1 and became secure

AdFullSsl supports creatives served by Google’s DoubleClick for Publishers (DFP). A creative is an actual ad displayed in web pages.

## Installation

<small>This software was tested on Python 2.6.6 on x86_64 Linux 2.6 Red Hat Enterprise 6.1.</small>

1. Check out a package of AdFullSsl:
    <pre>$ git clone https://github.com/linkedin/adfullssl.git</pre>
2. Install the installation tools for python. Please use the package manager installed on your environment:
    <pre>$ yum install python-pip</pre>
3.  Install python packages:
    <pre>$ pip install -r requirements.txt</pre>
4.  Install a Flash-supported version of PhantomJS from [r3b/phantomjs]. Please make sure that the flash support works fine with the example script on [ryanbridges.org].
5.  To configure authentication for DFP API, check out [googleads-python-legacy-lib] and run `adspygoogle/scripts/adspygoogle/dfp/config.py`. Two credential files `dfp_api_auth.pkl` and `dfp_api_config.pkl` will be created under your home directory.
6.  Create your private key to use for SSL and public x509 certificate, and move them to `scanner/baseline/keys`. The name of private key should be `privatekey.pem` and that of public x509 certificate should be `certificate.pem`. This is an example command to create these keys.
    <pre>
    $ openssl genrsa -out privatekey.pem 1024
    $ openssl req -new -key privatekey.pem -out certificate.csr
    $ openssl x509 -req -in certificate.csr -signkey privatekey.pem -out certificate.pem
    $ mv privatekey.pem certificate.pem conf/keys/
    </pre>

[r3b/phantomjs]: https://github.com/r3b/phantomjs
[ryanbridges.org]: http://www.ryanbridges.org/2013/05/21/putting-the-flash-back-in-phantomjs/
[googleads-python-legacy-lib]: https://github.com/googleads/googleads-python-legacy-lib

## Usage

1. Edit configuration file. Specify the path to your `phantomjs` command in the "phantomjs" parameter in the "Browser" section. Also, please set `False` to the items in the "Steps" section if you do not need to run them.
    <pre>$ vi conf/config.ini</pre>
2. Run the scanner:
    <pre>$ python src/adscan/run.py</pre>

### Set cookies

Cookies stored in files under the `conf/cookies` directory are used while browsing ads. The file name should be the domain name the cookies belong to. The cookies can be defined as the file content and each cookie are delimited by a semi-colon.

For example, cookies in `scanner/baseline/cookies/www.example.com.txt` file belong to `www.example.com` and its content is like this:
<pre>
xxx="abc=0000000000000000000000"; yyy="version=1111111111111111111"; SESSIONID="00000000000000000000";
</pre>

## How it works

### Overall steps

The scanner executes the following steps:

Step                   | Summary
-----------------------|------------------------------------------------------------------------
Download creative ids  | Download ids of recently-served creatives via ReportService of DFP API
Donwload creatives     | Download creative via CreativeService of DFP API
Modify creatives       | See the next section for the detail about how to modify creatives
Browse ads over HTTPS  | Host creatives on HTTPS server and browse them with headless browsers
Browse ads over HTTP   | Host creatives on HTTP server and browse them with headless browsers
Check SSL compliance   | Detect HTTP requests and compare the number of requests over HTTPS and HTTP
Upload creatives       | Upload creatives if they become compliant after modification via CreativeService of DFP API
Compress log file      | Compress the log directory at the end of the scanning process

### Browsing steps

The steps for browsing ads include the following steps:

Step                                | Summary
------------------------------------|----------------------------------------------------------------------
Load cookies                        | Load customized cookies to the headless browser.
Browse ads and capture all requests | Browse ads with the headless browser. The browser ignores all SSL certificate errors and captures all the request the ads make.
Check HTTPS availability            | Send a request to each requested URL captured in the previous step. The browser can recognize SSL certificate errors as well as other types of errors such as 4xx client-side errors and 5xx server-side errors, so that to identify the HTTPS availability on the servers.<br>If the requested URLs were made over HTTP in the previous step, these protocols are changed to HTTPS in this step and check if the HTTPS urls are available or not.

### Creative modification rule

We use *snippet* as a term meaning an HTML tag or a URL, which contains ad content. A snippet can be downloaded via DFP API, and we modify them to make them SSL compliant.

AdFullSsl basically replaces insecure `http:` protocol of hardcoded URLs with secure `https:` protocol or relative protocol. A relative protocol is a protocol that is the same protocol as the hosting page. The URL that has a relative protocol begins with `//`.

#### How to modify snippet

Snippet can be either HTML tags or a URL or a file name. We follow the rules below to modify snippet.

**HTML tags**

Execute these 2 steps:

1. Replace `http:` with a relative protocol if a URL match the following selectors:
    * `*[src]`: external object of img, embed, video, audio, svg, etc
    * `*[background]`: background image
    * `link[href][rel=stylesheet]`: css style sheet
    * `object[data]`: external object source
    * `applet[code]`: applet source
2. Replace `http:` with a relative protocol if a URL appears in element body of `<script>` or `<style>` tags:
    * Skip if the script dynamically creates tags that do not fetch external resources. For example, the URL in this code `document.write('<a href=url>')` does not need to be changed. But we need to change the URL of this code: `document.write('<img src=url>')`.

**URLs**

* Replace `http:` with `https:`

**File name**

* Do nothing

#### Modify element by creative types

DFP defines many type of creatives and their snippets appear in different elements by creative types. The table below shows which element contains a snippet or its equivalent that needs to be modified for making them ssl compliant.

Creative Type      | Snippet             |  Comment
-------------------|---------------------|---------------------------------------------------------
ThirdPartyCreative | `creative['snippet']` | **Modify URLs in snippet and scan expanded snippet**<br>ThirdPartyCreative has a snippet and an expanded snippet. A snippet can be editable so we can modify URLs in this element. An expanded snippet is read-only but it is closer to the actual HTML tags displayed on web pages than the snippet. AdFullSsl replaces the URLs appearning both in the snippet and expanded snippet, and scans only the expanded snippet.
AdExchangeCreative | `creative['codeSnippet']` | This element contains HTML tags.
AdSenseCreative | `creative['codeSnippet']` |This element contains HTML tags.
CustomCreative | `creative['htmlSnippet']` | This element contains HTML tags.
FlashCreative | `creative['previewUrl']` | **Modify nothing and scan preview HTML**<br>FlashCreative has a flashName element that contains the file name of the flash file displayed on web pages. We cannot edit this flash file. For scannnig, we download the actual HTML code from the preview url. Even after the scan detects insecure requests, we only report this creative as insecure because we do not know how to fix the flash file.
ImageCreative | `creative['primaryImageAsset']['assetUrl']` | Check SSL compliance of only this url because ads does not load other contents.
InternalRedirectCreative | `creative['internalRedirectUrl']` | Check SSL compliance of only this url because ads does not load other contents.
ImageRedirectCreative | `creative['imageUrl']` | Check SSL compliance of only this url because ads does not load other contents.
TemplateCreative | `creative['previewUrl']` | **Replace URL with https: instead of a relative protocol**<br>The `http:` should be replaced with `https:` for TemplateCreative because `https://` will be attached at the beginning of a URL if the URL does not start with a `http`. <br><br>**Modify only URLs appearing in creativeTemplateVariableValues element and scan preview HTML**<br>TemplateCreative has a creativeTemplateVariableValues element that contains URLs embedded into a creative template to make HTML code. Since the HTML can be downloaded by browsing the preview URL, we only modify URLs appearing in both creativeTemplateVariableValues element and the HTML downloaded from the preview URL.

## Data stored in the database

The scanner saves the scan logs in the database.

Table name     | Columns or content
---------------|-------------------------
cretive        | 1. created date<br>2. updated date<br>3. creative id<br>4. creative type <small>(The creative type used in DFP)</small><br>5. preview url <small>(The URL to view the creative in an HTML page)</small><br>6. modification status <small>(True: modified, False unmodified)</small><br>7. snippet <small>(an HTML tag or URL to show ads)</small><br>8. modified snippet <small>(a snippet modified by AdFullSsl to make SSL compliant)</small><br>9. expanded snippet <small>(another snippet used in ThirdPartyCreative)</small><br>10. SSL compliance  <small>(True: compliant, False: non-compliant)</small><br>11. request match status  <small>(True: matched, False: mismatched)</small><br>12. uploaded status  <small>(True: uploaded, False: not uploaded)</small>
creative_cache | 1. created date<br>2. updated date<br>3. creative id<br>4. creative type <small>(The creative type used in DFP)</small><br>5. preview url <small>(The URL to view the creative in an HTML page)</small><br>6. snippet <small>(an HTML tag or URL to show ads)</small><br>7. expanded snippet <small>(another snippet used in ThirdPartyCreative)</small>
scanlog        | 1. created date<br>2. updated date<br>3. creative id<br>4. issue id <small>(See below&ast;)</small><br>5. requested URL <small>(The URL to which requests are made)</small><br>6. protocol <small>(`https` or `http`: the protocol used in the scanning process)</small>

&ast;issue id is one of these; 0: no issue found, 1: invalid SSL certificate was found, 2: no SSL server was available, 3: HTTP request was made to the server that supports HTTPS, 4: 4xx client-side error found, 5: 5xx server-side error found, and 9: no external request was made.
</small>

These are examples of some useful SQL queries to extract information from the database.

* Number of creatives scanned on 2014-05-01:
  <pre>select count(*) from creative where created_at='2014-05-01';</pre>
* Creatives that will become SSL compliant after modification on 2014-05-01:
  <pre>select creative_id from creative where created_at='2014-05-01' and compliance=1 and modified=1;</pre>
* Creatives that will become SSL compliant after modification but the numbers of request over HTTPS and HTTP did not match on 2014-05-01:
  <pre>select creative_id from creative where created_at='2014-05-01' and compliance=1 and modified=1 and request_match=0;</pre>
* SSL compliant creatives that are uploaded to DFP on 2014-05-01:
  <pre>select creative_id from creative where created_at='2014-05-01' and uploaded=1;</pre>
* SSL non-compliant creatives on 2014-05-01:
  <pre>select creative_id from creative where created_at='2014-05-01' and compliance=0;</pre>
* URLs to which creatives made HTTP requests or invalid requests on 2014-05-01:
  <pre>select creative_id, url from scanlog where created_at='2014-05-01' and protocol='https' and issue_id!=0 and issue_id!=0;</pre>

## Tests

Install nose and run `nosetests` command:

<pre>
$ pip install nose
$ nosetests
</pre>

Please make sure that all the installation step above are completed before starting the tests. The test case loads the config file and one of the test case verifies if the phantomjs captures requests made by a flash content.

## License

Copyright 2014 LinkedIn Corporation.

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.

The license information on third-party code is included in `NOTICE`.
