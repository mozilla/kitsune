---
title: Other Notes
---

::: warning
::: title
Warning
:::

This section of documentation may be outdated.
:::

# Questions

## memcached

::: note
::: title
Note
:::

This should probably be somewhere else, but the easy way to flush your
cache is something like this:

    echo "flush_all" | nc localhost 11211

Assuming you have memcache configured to listen to 11211.
:::
