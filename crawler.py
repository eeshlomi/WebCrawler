#!/usr/bin/python

__author__ = 'eeshlomi'
__version__ = '1.0'

import sys
try:
    import os
    import time
    import re
    import requests
    import traceback
    from bs4 import BeautifulSoup, SoupStrainer
except ImportError:
    msg = "\nPython %s\n\nModule import error:\n%s\n"
    sys.exit(msg % (sys.version, sys.exc_info()[1]))


def crawler_run(url, orig_depth, cur_depth, processed_list, rated_list):
    _depth = 1 + orig_depth - cur_depth
    print("%s(%d): Checking..." % (url, _depth))
    processed_list.append(url)
    try:
        r = requests.head(url, allow_redirects=True)
        if r.headers['content-type'][:9] != "text/html":
            return "%s(%d) skipped: Not a text/html page." % (url, _depth)
    except KeyError:
        msg = "%s(%d) skipped: No content-type header"
        return msg % (url, _depth)
    except requests.exceptions.ConnectionError:
        return "%s(%d) skipped: Not found." % (url, _depth)
    except requests.exceptions.SSLError:
        return "%s(%d) skipped: SSL certificate mismatch." % (url, _depth)
    except requests.exceptions.MissingSchema:
        msg = "Halted: %s does not include preceding http/s\n"
        return msg % (url)  # Bad URL in input(DEPTH as in input)
    # "[1]" would've been faster but it fails with missing "//":
    cachefile = url.split("//")[-1].replace("/", "_")
    domain = cachefile.split("_")[0]
    cachefile = "tmp_cache/"+cachefile
    tslocal = tsonline = 0
    if os.path.isfile(cachefile):
        tslocal = os.stat(cachefile).st_mtime
        try:
            tsonline = time.mktime(time.strptime(r.headers['Last-Modified'], "%a, %d %b %Y %H:%M:%S %Z"))
        # Header doesn't exist or has unknown format. Give a 24-hour TTL:
        except(KeyError, ValueError):
            if(tslocal + 86400) < time.time():
                tslocal = 0
    # Also true if both are the same, because of the download timestamp:
    if(tslocal > tsonline):
        print("%s(%d): Found locally." % (url, _depth))
    else:
        r = requests.get(url, allow_redirects=True)
        open(cachefile, 'w').write(r.content)
    print("%s(%d): Extracting links..." % (url, _depth))
    _next_depth = cur_depth-1
    _intern_cnt = 0
    _extern_cnt = 0
    with open(cachefile, 'r') as f:
        for link in BeautifulSoup(f.read(), parse_only=SoupStrainer('a'), features='html.parser'):
            if link.has_attr('href'):
                _next_url = re.split(r'#|\?', link['href'])[0]
                _next_domain = _next_url.split("//")[-1].split("/")[0]
                if _next_domain == domain or link['href'][:4] != "http":
                    _intern_cnt += 1
                else:
                    _extern_cnt += 1
                    try:
                        if(_next_depth > 0) and _next_url not in processed_list:
                            print(crawler_run(_next_url, orig_depth, _next_depth, processed_list, rated_list))
                    # For a non-handled error, show Traceback and continue the recursion:
                    except Exception:
                        print(traceback.format_exc())
        try:
            _ratio = round(float(_intern_cnt) / (_intern_cnt + _extern_cnt), 2)
        except ZeroDivisionError:
            _ratio = 1
        rated_list.append("%s\t%d\t%s" % (url, _depth, _ratio))
        return "%s(%d) Finished." % (url, _depth)


def crawler(url, depth):
    os.path.isdir("tmp_output") or os.mkdir("tmp_output")
    os.path.isdir("tmp_cache") or os.mkdir("tmp_cache")
    outputfile = "tmp_output/"+url.split(r'#|\?')[0].split("//")[-1].replace("/", "_")+"_"+str(depth)+".output"
    processed_list = []
    rated_list = []
    if os.path.isfile(outputfile):
        print("\nAn output file was found, resuming...\n")
        with open(outputfile) as f:
            for line in f:
                processed_list.append(line.split('\t')[0])
                # rated_list is reversed upon save-to-disk:
                rated_list.insert(0, line.split('\n')[0])
    url = re.split(r'#|\?', url)[0]
    try:
        if(depth > 0) and url not in processed_list:
            print(crawler_run(url, depth, depth, processed_list, rated_list))
    except KeyboardInterrupt:
        print("\nStopped.(Run again to resume)")
    print("\nPlease wait while saving gathered rates...")
    with open(outputfile, 'w') as f:
        for item in tuple(reversed(rated_list)):  # Get depth 1 first.
            ''' Had the list been built from file upon resumption,
            it wouldn't have the "\n".
            That's why I don't include it in the list itself: '''
            f.write(item+"\n")
    return("\nOutput file is %s\n" % (outputfile))


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit("Usage: %s <url> <depth>" % (sys.argv[0]))
    try:
        print(crawler(sys.argv[1], int(sys.argv[2])))
    except ValueError:
        sys.exit("<depth> must be integer")
