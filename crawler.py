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


def c_run(url, o_depth, c_depth, skip, rated):
    # By stripping the optional trailing "/",
    # we use the cache more efficiently:
    if url[-1] == "/":
        url = url[:len(url)-1]
    _depth = 1 + o_depth - c_depth
    print("%s(%d): Checking..." % (url, _depth))
    skip.append(url)
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
            t_string = r.headers['Last-Modified']
            t_struct = time.strptime(t_string, "%a, %d %b %Y %H:%M:%S %Z")
            tsonline = time.mktime(t_struct)
        except KeyError:
            msg = "%s(%d): No Last-Modified header, giving a 24-hour TTL."
            print(msg % (url, _depth))
            if(tslocal + 86400) < time.time():
                tslocal = 0
        except ValueError:
            msg = "%s(%d): Unknown format %s, giving a 24-hour TTL."
            print("%s(%d): ." % (url, _depth, t_string))
            if(tslocal + 86400) < time.time():
                tslocal = 0
    # Also true if both are the same, because of the download timestamp:
    if(tslocal > tsonline):
        print("%s(%d): Found locally." % (url, _depth))
    else:
        r = requests.get(url, allow_redirects=True)
        open(cachefile, 'wb').write(r.content)
    print("%s(%d): Extracting links..." % (url, _depth))
    n_depth = c_depth-1
    _intern_cnt = 0
    _extern_cnt = 0
    with open(cachefile, 'r') as f:
        for link in BeautifulSoup(f.read(), parse_only=SoupStrainer('a'), features='html.parser'):
            if link.has_attr('href'):
                n_url = re.split(r'#|\?', link['href'])[0]
                n_domain = n_url.split("//")[-1].split("/")[0]
                if n_domain == domain or link['href'][:4] != "http":
                    _intern_cnt += 1
                else:
                    _extern_cnt += 1
                    try:
                        if(n_depth > 0) and n_url not in skip:
                            print(c_run(n_url, o_depth, n_depth, skip, rated))
                    # For a non-handled error,
                    # show Traceback and continue the recursion:
                    except Exception:
                        print(traceback.format_exc())
        try:
            _ratio = round(float(_intern_cnt) / (_intern_cnt + _extern_cnt), 2)
        except ZeroDivisionError:
            _ratio = 1
        rated.append("%s\t%d\t%s" % (url, _depth, _ratio))
        return "%s(%d) Finished." % (url, _depth)


def crawler(url, depth):
    url = re.split(r'#|\?', url)[0]
    # The following is for returning the proper filename:
    if url[-1] == "/":
        url = url[:len(url)-1]
    os.path.isdir("tmp_output") or os.mkdir("tmp_output")
    os.path.isdir("tmp_cache") or os.mkdir("tmp_cache")
    outputfile = "tmp_output/" + url.split("//")[-1].replace("/", "_")
    outputfile += "_" + str(depth) + ".output"
    skip = []
    rated = []
    if os.path.isfile(outputfile):
        print("\nAn output file was found, resuming...\n")
        with open(outputfile) as f:
            for line in f:
                skip.append(line.split('\t')[0])
                # rated is reversed upon save-to-disk:
                rated.insert(0, line.split('\n')[0])
    try:
        if(depth > 0) and url not in skip:
            print(c_run(url, depth, depth, skip, rated))
    except KeyboardInterrupt:
        print("\nStopped.(Run again to resume)")
    print("\nPlease wait while saving gathered rates...")
    with open(outputfile, 'w') as f:
        for item in tuple(reversed(rated)):  # Get depth 1 first.
            ''' Had the list been built from file upon resumption,
            it wouldn't have had the "\n".
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
