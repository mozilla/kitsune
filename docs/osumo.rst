.. _osumo-chapter:

============
Offline SUMO
============

The primary documentation for offline sumo lives here:
https://osumo.readthedocs.org. The source lives at
https://gihub.com/mozilla/osumo.

Offline SUMO requires a component on Kitsune and this component relies heavily
on Redis as we generate all the articles once a day and put it into
Kitsune. Make sure that is available.

The code for offline sumo's bundle generation lives under
`kitsune/offline`. Inside, there are a couple of files defined:

- utils.py does the actual bundle generation.
- index.py is responsible for generating the index for offline search.
- urls.py defines the url for Django.
- views.py implements the two views.
- cron.py has the cron job that runs daily for bundle generation.
- tests/ has unittests.
