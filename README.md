# Why

Want to reproduce a request from the browser with the most concise `curl` command? "Copy as cURL" in your browser and paste it as arguments to `curl2min`. The minimal `curl` statement will be output to stdout.

# How

`curl2min` makes repeated requests to determine which curl parameters have no impact on the response status code and content. This makes it sensitive to request parameters that become invalid (e.g. expiring session cookies) and sites with request-independent dynamic content. The main algorithm is a leave-one-out strategy which assumes that curl parameters do not interact in sophisticated ways (e.g. a site that responds different if both header A and B are absent but responds the same if only header A or header B are absent).

# Install

```bash
pip install curl2min
```
# Example

This is a real-world example of an authenticated request. Which of the 25 cookies and 10 other headers are required for a successful response? It turns out only two of the cookies and one of the other headers are required.

## curl before

```curl 'https://REDACTED/store/myaccount/profile.jsp?selpage=MY+PROFILE' -H 'User-Agent: REDACTED' -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8' -H 'Accept-Language: en-US,en;q=0.5' --compressed -H 'Referer: REDACTED' -H 'Connection: keep-alive' -H 'Cookie: o59a9A4Gx=REDACTED; _gcl_au=REDACTED; _ga_3NXP3C8S9V=REDACTED; _ga=REDACTED; _fbp=REDACTED; kampyleUserSession=REDACTED; kampyleSessionPageCounter=REDACTED; kampyleUserSessionsCount=REDACTED; _pin_unauth=REDACTED; _pin_unauth=REDACTED; mab_usps=REDACTED; uspsstaticwebpop=REDACTED; TLTSID=REDACTED; reg-entreg=REDACTED; EntRegName=REDACTED; EntRegPrefs=REDACTED; JSESSIONID=REDACTED; psSessionExpiry=REDACTED; NSC_jou-blbnbj-tupsf-xbt9-mc=REDACTED; EntReg=REDACTED; EntRegEX=REDACTED; TINTCYALF=REDACTED; DYN_USER_ID=REDACTED; DYN_USER_CONFIRM=6REDACTED' -H 'Upgrade-Insecure-Requests: 1' -H 'Pragma: no-cache' -H 'Cache-Control: no-cache' -H 'TE: Trailers'```

## curl after

This is what is output to stdout:

```curl 'https://store.usps.com/store/myaccount/profile.jsp?selpage=MY+PROFILE' -H 'User-Agent: REDACTED' -H 'Cookie: JSESSIONID=REDACTED; NSC_jou-blbnbj-tupsf-xbt9-mc=REDACTED; TINTCYALF=REDACTED'```

## curl2min command

Running curl2min is a matter of appending the curl command as arguments:

```curl2min curl ...all the original curl arg bloat same as above...```

## Verbose output

This is the verbose output to stderr (which you can suppress with `-q`):

```
Testing for identical results...
Testing with minimum arguments...
Testing with leave one out...
Required: ['-H', 'User-Agent: REDACTED']
Not required: ['-H', 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9, ...
Not required: ['-H', 'Accept-Language: en-US,en;q=0.5']
Not required: ['--compressed']
Not required: ['-H', 'Referer: REDACTED']
Not required: ['-H', 'Connection: keep-alive']
Required: ['-H', 'Cookie: o59a9A4Gx=REDACTED; _gcl_au=REDACTED; _ga_3NXP3C8S9V=REDACTED; ...
Not required: ['-H', 'Upgrade-Insecure-Requests: 1']
Not required: ['-H', 'Pragma: no-cache']
Not required: ['-H', 'Cache-Control: no-cache']
Not required: ['-H', 'TE: Trailers']
Verifying leave one out work inferences work in combination...
Verifying cookies disassemble and reassemble...
Testing with leave one out for cookies...
Not required: Cookie: o59a9A4Gx=REDACTED
Not required: Cookie: _gcl_au=REDACTED
Not required: Cookie: _ga_3NXP3C8S9V=REDACTED
Not required: Cookie: _ga=REDACTED
Not required: Cookie: _fbp=REDACTED
Not required: Cookie: kampyleUserSession=REDACTED
Not required: Cookie: kampyleSessionPageCounter=REDACTED
Not required: Cookie: kampyleUserSessionsCount=REDACTED
Not required: Cookie: _pin_unauth=REDACTED
Not required: Cookie: _pin_unauth=REDACTED
Not required: Cookie: mab_usps=REDACTED
Not required: Cookie: uspsstaticwebpop=REDACTED
Not required: Cookie: TLTSID=REDACTED
Not required: Cookie: reg-entreg=REDACTED
Not required: Cookie: EntRegName=REDACTED
Not required: Cookie: EntRegPrefs=REDACTED
Required: Cookie: JSESSIONID=REDACTED
Not required: Cookie: psServerTime=REDACTED
Not required: Cookie: psSessionExpiry=REDACTED
Not required: Cookie: NSC_jou-blbnbj-tupsf-xbt9-mc=REDACTED
Not required: Cookie: EntReg=REDACTED
Not required: Cookie: EntRegEX=REDACTED
Required: Cookie: TINTCYALF=REDACTED
Not required: Cookie: DYN_USER_ID=REDACTED
Not required: Cookie: DYN_USER_CONFIRM=REDACTED
Verifying leave one out work inferences work in combination for cookies...
Success!
```

# Advanced usage

Usage is:

```
Usage: curl2min [options] curl [curl_arguments]

Strip a curl statement down to it's essential arguments.

Options:
  -h, --help            show this help message and exit
  -q, --quiet           don't print status messages to stdout
  -s STATUS, --expected-status=STATUS
                        require resulting status code to be STATUS
```

## --quiet

This makes it so that the only output to stderr will then be actual errors.

## --expected-status=STATUS

This guards against an initially failing curl command. Specify what the status code of the initial request is to protect against this.

# Troubleshooting

## Status was XXX not the expected 200

* Is a XXX status code expected for the original curl? If yes, specify the status code using `--expected-status=302`.
* Is a XXX status code unexpected? It may be that a cookie value is no longer valid. Try again with a fresh curl captured from your browser.

## Status codes vary across identical requests

A key assumption is that identical curl requests will have identical responses. It could be that between the first and second calls a cookie value became invalid. Try again with a fresh curl captured from your browser.

## Response content varies across identical requests

A key assumption is that identical curl requests will have identical responses. It could be that between the first and second calls a cookie value became invalid. Try again with a fresh curl captured from your browser.

## Leave one out assumption for headers failed

If leaving out header A still works, and leaving out header B still works, then a key assumption that leaving out header A and B will still work. This failure message implies that assumption does not hold for the original curl. It could be that between calls a cookie value became invalid. Try again with a fresh curl captured from your browser.

## Cookie disassemble and reassemble assumption failed

Is suggests a logic failure in the script. Much more likely is that between calls a cookie value became invalid. Try again with a fresh curl captured from your browser.

## Leave one out assumption for cookies failed

If leaving out cookie A still works, and leaving out cookie B still works, then a key assumption that leaving out cookie A and B will still work. This failure message implies that assumption does not hold for the original curl. It could be that between calls a cookie value became invalid. Try again with a fresh curl captured from your browser.
