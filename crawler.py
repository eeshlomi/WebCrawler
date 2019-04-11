#!/usr/bin/python2.7

__author__ = 'Shlomi Ratsabbi'
__version__ = '1.0'

import sys
try:
  import optparse, os, time, re, requests, traceback
  from bs4 import BeautifulSoup, SoupStrainer
except ImportError:
  print >> sys.stderr, "\nPython %s\n\nModule import error:\n%s\n" % (sys.version, sys.exc_value)
  sys.exit(1)

conf = {'url': None, 'depth': None}

def cli_reader():
  optp = optparse.OptionParser()
  optp.add_option('-u', '--url', help='URL of the root page', dest='url')
  optp.add_option('-d', help='recursion depth limit', dest='depth', type="int")
  opts, args = optp.parse_args()
  if opts.url and opts.depth:
    conf['url'] = opts.url
    conf['depth'] = opts.depth
  else:
    print >> sys.stderr, "A url and depth are required!"
    optp.print_help()
    sys.exit(1)

def crawler(url, depth):
  _depth = 1+conf['depth']-depth
  print "%s (%d): Checking..." % (url, _depth)
  processed_list.append(url)
  try:
    r = requests.head(url, allow_redirects=True)
    if r.headers['content-type'][:9] != "text/html":
      return "%s (%d) skipped: Not a text/html page." % (url, _depth)
  except KeyError:
    return "%s (%d) skipped: Could not determine whether it contains text/html." % (url, _depth)
  except requests.exceptions.ConnectionError:
    return "%s (%d) skipped: Not found." % (url, _depth)
  except requests.exceptions.SSLError:
    return "%s (%d) skipped: SSL certificate mismatch." % (url, _depth)
  except requests.exceptions.MissingSchema:
    return "Halted: %s is not a valid URL. Please include preceding http/s\n" % (url) #Bad URL in input (DEPTH as in input)
  cachefile=url.split("//")[-1].replace("/", "_") # "[1]" would've been faster but it fails with missing "//"
  domain=cachefile.split("_")[0]
  cachefile="tmp_cache/"+cachefile
  tslocal = tsonline = 0
  if os.path.isfile(cachefile):
    tslocal = os.stat(cachefile).st_mtime
    try:
      tsonline = time.mktime(time.strptime(r.headers['Last-Modified'], "%a, %d %b %Y %H:%M:%S %Z"))
    except KeyError, ValueError: # Header doesn't exist or has unknown format. Give a 24-hour TTL
      if (tslocal+86400) < time.time(): tslocal = 0
  if (tslocal > tsonline): # Also true if both have the same version, because download timestamp is higher.
    print "%s (%d): Found locally." % (url, _depth)
  else:
    r = requests.get(url, allow_redirects=True)
    open(cachefile, 'w').write(r.content)
  print "%s (%d): Extracting links..." % (url, _depth)
  _next_depth = depth-1
  _intern_cnt = 0
  _extern_cnt = 0
  with open(cachefile,'r') as f:
    for link in BeautifulSoup(f.read(), parse_only=SoupStrainer('a'), features='html.parser'):
      if link.has_attr('href'):
        _next_url=re.split('#|\?',link['href'])[0]
        _next_domain=_next_url.split("//")[-1].split("/")[0]
        if _next_domain==domain or link['href'][:4]!="http":
          _intern_cnt += 1
        else:
          _extern_cnt += 1
          try:
            if (_next_depth > 0) and _next_url not in processed_list: print crawler(_next_url, _next_depth)
          except Exception as exc: #For a non-handled error, show Traceback and continue the recursion:
            print traceback.format_exc()
    try:
      _ratio=round (float (_intern_cnt) / ( _intern_cnt+_extern_cnt ), 2)
    except ZeroDivisionError:
      _ratio=1
    rated_list.append("%s\t%d\t%s" % (url, _depth, _ratio))
    return "%s (%d) Finished." % (url, _depth)

cli_reader()
os.path.isdir("tmp_output") or os.mkdir("tmp_output", 0755)
os.path.isdir("tmp_cache") or os.mkdir("tmp_cache", 0755)
outputfile = "tmp_output/"+conf['url'].split('#|\?')[0].split("//")[-1].replace("/", "_")+"_"+str(conf['depth'])+".output"
processed_list = [] #Differs from rated_list, being created immediately to prevent re-processing the same URL within recursion.
rated_list = []
if os.path.isfile(outputfile):
  print "\nAn output file was found, resuming...\n"
  with open(outputfile) as f:
    for line in f:
      processed_list.append(line.split('\t')[0])
      rated_list.insert(0, line.split('\n')[0]) #List is reversed upon save-to-disk
url = re.split('#|\?',conf['url'])[0]
try:
  if (conf['depth'] > 0) and url not in processed_list: print crawler(url, conf['depth'])
except KeyboardInterrupt, e:
  print "\nStopped. (Run again to resume)"
print "\nPlease wait while saving gathered rates..."
with open(outputfile, 'w') as f:
  for item in tuple(reversed(rated_list)): #Get depth 1 first.
    f.write(item+"\n") #Had the list built from file upon resumption it wouldn't have the "\n". That's why I don't include it in the list itself.
print "\nOutput file is %s\n" % (outputfile)

