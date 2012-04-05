=======================
Service Level Agreement
=======================

This isn't a zero-tolerance policy, but a series of policy points we
work towards when making changes to the site.

Measurements are based on what we can see in graphite which means it's
all server-side. Also, we use the upper_90 line since that tracks the
more extreme side of performance.

This SLA will probably change over time. Here it is now.

1. View performance

   upper_90 for server-side rendering of views for GET requests should
   be under 800ms.

2. Search view performance

   upper_90 for server-side rendering of search views should be under
   1000ms.

3. Search availability

   Search should work and return useful results.

   The implication here is that it's not ok to be reindexing into an
   index that searches are against.

4. Browser support

   See this page in the wiki:

   https://wiki.mozilla.org/Support/Browser_Support
