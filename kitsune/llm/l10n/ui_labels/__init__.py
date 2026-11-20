"""
Official translations for the UI labels in Knowledge Base articles.

An article often names a menu, a button, or another part of a user interface (UI). That
can be the interface of an app, a website or an operating system. The article writes the
name inside {menu …}, {button …} or {pref …}, like {menu Settings}. This package finds
how the product itself shows each of them in a locale, and machine translation writes
that, so that a translated article says what its reader's screen says.

Words used throughout:

- A label is the text inside {menu}, {button} or {pref}.
- A use is one {menu …}, {button …} or {pref …} in an article. Most hold a label.
  A {pref} can also hold text a product never translates, like a preference's name.
- A label's position is its place among all the uses of an article, counting from 0.
- An official label is a label as its product shows it in one locale: "Paramètres"
  for {menu Settings} in French.
- An owner is the app or website whose screen shows a label, like Firefox or
  addons.mozilla.org.
- A string is one piece of text in a product. It has an ID, and a translation in
  each locale the product ships, which means each language it is released in.
- A source is a repository where products keep their strings.
- A catalog is all of one owner's strings in one locale.
- A spot is a group of an owner's strings that share their English text and are
  translated the same way in every locale. "View" in the menu bar and "View" on
  a button are two spots if any locale translates them differently.
"""
