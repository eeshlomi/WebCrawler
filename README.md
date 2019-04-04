# WebCrawler
 Calculates the ratio of same­-domain links in a given root-page, plus a recursion depth limit.

## Features

 WebCrawler should be executed with two arguments­: the URL of the root page, and the recursion depth limit (a positive integer).

 Only text/html pages are processed, being downloaded to a temp directory and their links are examined. A depth limit of 1 means that only the URL given to WebCrawler upon execution will be processed.

 If a page has, for example, 4 same--domain links and 1 external link, then its ratio will be 0.8.

 Has the WebCrawler terminated by the user (Ctrl+C), It caches the collected info to be resumed at the next run.

 The output is a Tab Separated File, containing URL, depth, and ratio.
