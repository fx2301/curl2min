import hashlib
import json
from optparse import OptionParser
import os
import re
import subprocess
import sys
import typing

def main():
    parser = OptionParser('usage: %prog [options] curl [curl_arguments]')
    parser.description = 'Strip a curl statement down to it\'s essential arguments.'
    parser.add_option("-q", "--quiet",
                    action="store_false", dest="verbose", default=True,
                    help="don't print status messages to stdout")
    parser.add_option("-s", "--expected-status", dest="expected_status", default=200, type="int",
                    help="require resulting status code to be STATUS", metavar="STATUS")

    try:
        curl_index = sys.argv.index('curl')
        args = sys.argv[1:curl_index]
    except ValueError as e:
        args = sys.argv[1:]
        
    (options, remaining_args) = parser.parse_args(args=args)
    if len(remaining_args) > 0:
        parser.error(f'Unexpected argument(s): {" ".join(remaining_args)}')

    cmd = sys.argv[curl_index:]

    log = sys.stderr if options.verbose else open(os.devnull, 'w')
    err = sys.stderr

    def fail(msg):
        err.write('Aborting. ')
        err.write(msg)
        err.write(' See https://github.com/fx2301/curl2min#Troubleshooting\n')
        exit(1)

    # Scraped via:
    # man curl | grep -E '^\s+-.*<[a-z]+' | cut -d'<' -f1 | tr , '\n' | sed 's/^ *//' | cut -d' ' -f1 | xargs -I {} printf "\t'{}',\n"
    CURL_PAIRED_ARGS = [
        '--abstract-unix-socket', '--alt-svc', '--aws-sigv4', '--cacert', '--capath', '--cert-type', '-E', '--cert', '--ciphers', '-K', '--config', '--connect-timeout', '-C', '--continue-at', '-c', '--cookie-jar', '-b', '--cookie', '--create-file-mode', '--crlfile', '--curves', '--data-ascii', '--data-binary', '--data-raw', '--data-urlencode', '-d', '--data', '--dns-interface', '--dns-ipv4-addr', '--dns-ipv6-addr', '--dns-servers', '-D', '--dump-header', '--egd-file', '--engine', '--etag-compare', '--etag-save', '--expect100-timeout', '--form-string', '-F', '--form', '-F', '--ftp-account', '--ftp-alternative-to-user', '--ftp-method', '-P', '--ftp-port', '--ftp-ssl-ccc-mode', '--happy-eyeballs-timeout-ms', '-H', '--header', '-h', '--help', '--hostpubmd5', '--hostpubsha256', '--hsts', '--interface', '--keepalive-time', '--key-type', '--key', '--krb', '--libcurl', '--limit-rate', '--local-port', '--login-options', '--mail-auth', '--mail-from', '--mail-rcpt', '--max-filesize', '--max-redirs', '-m', '--max-time', '--netrc-file', '--noproxy', '--oauth2-bearer', '--output-dir', '-o', '--output', '--parallel-max', '--pass', '--pinnedpubkey', '--proto-default', '--proto-redir', '--proto', '--proxy-cacert', '--proxy-capath', '--proxy-cert-type', '--proxy-cert', '--proxy-ciphers', '--proxy-crlfile', '--proxy-header', '--proxy-key-type', '--proxy-key', '--proxy-pass', '--proxy-pinnedpubkey', '--proxy-service-name', '--proxy-tls13-ciphers', '--proxy-tlsauthtype', '--proxy-tlspassword', '--proxy-tlsuser', '-U', '--proxy-user', '--proxy1.0', '--pubkey', '-Q', '--quote', '--random-file', '-r', '--range', '--request-target', '-X', '--request', '--retry-delay', '--retry-max-time', '--retry', '--sasl-authzid', '--service-name', '--socks4', '--socks4a', '--socks5-gssapi-service', '--socks5-hostname', '--socks5', '-Y', '--speed-limit', '-y', '--speed-time', '--stderr', '-t', '--telnet-option', '--tftp-blksize', '-z', '--time-cond', '--tls13-ciphers', '--tlsauthtype', '--tlspassword', '--tlsuser', '--trace-ascii', '--trace', '--unix-socket', '-T', '--upload-file', '--url', '-A', '--user-agent', '-u', '--user', '-w', '--write-out'
    ]

    arguments = []
    for i in range(1, len(cmd)):
        if cmd[i] in CURL_PAIRED_ARGS:
            continue
        if cmd[i] in ['-v', '--verbose']:
            continue
        if cmd[i] in ['-s', '--silent']:
            continue

        if cmd[i-1] in CURL_PAIRED_ARGS:
            arguments.append(cmd[i-1:i+1])
        else:
            arguments.append(cmd[i:i+1])

    arguments_required = [
        args
        for args in arguments
        if not args[0].startswith('-')
    ]
    arguments_undecided = [
        args
        for args in arguments
        if args[0].startswith('-')
    ]

    def execute_curl(arguments) -> typing.Tuple[int, str]:
        cmd = ['curl', '-v', '-s']
        for arg in arguments:
            cmd += arg
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout = proc.stdout.read()
        stderr = proc.stderr.read()

        status_match = re.search(r'^< HTTP/[0-9.]+ ([0-9]+)', stderr.decode('utf-8'), re.MULTILINE)
        if not status_match:
            raise Exception(f"No status found in response for: {cmd}")
        
        # TODO check for location header as well

        status = int(status_match[1])
        digest = hashlib.sha256(stdout).hexdigest()

        return status, digest
        
    log.write('Testing for identical results...\n')
    test_run1 = execute_curl(arguments_required + arguments_undecided)
    test_run2 = execute_curl(arguments_required + arguments_undecided)
    if test_run1[0] != test_run2[0]:
        fail(f'Status codes vary across identical requests: {test_run1[0]} vs {test_run2[0]}')

    if test_run1[1] != test_run2[1]:
        fail(f'Response content varies across identical requests: sha256sum {test_run1[1]} vs {test_run2[1]}')

    if test_run1[0] != options.expected_status:
        fail(f'Status was {test_run1[0]} not the expected {options.expected_status}. A cause of this could be expired cookies. Use --expected-status {test_run1[0]} if this is expected.')


    log.write('Testing with minimum arguments...\n')
    test_minimum = execute_curl(arguments_required)
    if test_minimum != test_run1:
        log.write('Testing with leave one out...\n')
        arguments_remaining = []
        for i in range(len(arguments_undecided)):
            test_leave_one_out = execute_curl(arguments_required + arguments_undecided[:i] + arguments_undecided[i+1:])
            if test_leave_one_out == test_run1:
                log.write(f'Not required: {arguments_undecided[i]}\n')
            else:
                log.write(f'Required: {arguments_undecided[i]}\n')
                arguments_remaining.append(arguments_undecided[i])

        log.write('Verifying leave one out work inferences work in combination...\n')
        test_leave_all_out = execute_curl(arguments_required + arguments_remaining)
        if test_leave_all_out != test_run1:
            fail('Leave one out assumption for headers failed! A cause of this could be expired cookies.')

        arguments_undecided = arguments_remaining

        cookie_headers = [
            arg[1]
            for arg in arguments_undecided
            if arg[0] == '-H' and arg[1].startswith('Cookie: ')
        ]
        arguments_required += [
            arg
            for arg in arguments_undecided
            if not(arg[0] == '-H' and arg[1].startswith('Cookie: '))
        ]
        arguments_undecided = None

        cookies_undecided = []
        for header in cookie_headers:
            m = re.match(r'^Cookie: (.*)$', header)
            assert m, f'Expected to extract cookies from header: {header}'
            cookies_undecided += m[1].split('; ')
        
        if len(cookies_undecided) > 0:
            log.write('Verifying cookies disassemble and reassemble...\n')
            cookie_header = f'Cookie: {"; ".join(cookies_undecided)}'
            test_cookie_reassemble = execute_curl(arguments_required + [['-H', cookie_header]])
            if test_cookie_reassemble != test_run1:
                fail('Cookie disassemble and reassemble assumption failed! A cause of this could be expired cookies.')

            log.write('Testing with leave one out for cookies...\n')
            cookies_remaining = []
            for i in range(len(cookies_undecided)):
                cookie_header = f'Cookie: {"; ".join(cookies_undecided[:i] + cookies_undecided[i+1:])}'
                test_leave_one_out = execute_curl(arguments_required + [['-H', cookie_header]])
                if test_leave_one_out == test_run1:
                    log.write(f'Not required: Cookie: {cookies_undecided[i]}\n')
                else:
                    log.write(f'Required: Cookie: {cookies_undecided[i]}\n')
                    cookies_remaining.append(cookies_undecided[i])

            log.write('Verifying leave one out work inferences work in combination for cookies...\n')
            arguments_required += [
                ['-H', f'Cookie: {"; ".join(cookies_remaining)}']
            ]
            test_leave_all_out = execute_curl(arguments_required)
            if test_leave_all_out != test_run1:
                fail('Leave one out assumption for cookies failed! A cause of this could be expired cookies.')

    log.write('Success!\n')
    log.write('Minimal curl is:\n')

    SINGLE_QUOTE_ESCAPE = '\'"\'"\''
    def quote_argument(arg):
        if not re.search(r'[^A-Za-z0-9_/-]', arg):
            return arg

        arg_escaped = arg.replace('\'', SINGLE_QUOTE_ESCAPE)
        return f"'{arg_escaped}'"

    cmd = ['curl']
    for args in arguments_required:
        cmd += [
            quote_argument(arg)
            for arg in args
        ]

    print(' '.join(cmd))

if __name__ == "__main__":
    main()
