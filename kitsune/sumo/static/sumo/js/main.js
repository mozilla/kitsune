export const getQueryParamsAsDict = function (url) {
  // Parse the url's query parameters into a dict. Mostly stolen from:
  // http://stackoverflow.com/questions/901115/get-query-string-values-in-javascript/2880929#2880929
  var queryString = '',
    splitUrl,
    urlParams = {},
    e,
    a = /\+/g,  // Regex for replacing addition symbol with a space
    r = /([^&=]+)=?([^&]*)/g,
    d = function (s) { return decodeURIComponent(s.replace(a, ' ')); };

  if (url) {
    splitUrl = url.split('?');
    if (splitUrl.length > 1) {
      queryString = splitUrl.splice(1).join('');
    }
  } else {
    queryString = window.location.search.substring(1);
  }

  e = r.exec(queryString);
  while (e) {
    urlParams[d(e[1])] = d(e[2]);
    e = r.exec(queryString);
  }
  return urlParams;
};

export const getReferrer = function (urlParams) {
  /*
    Get the referrer to the current page. Returns:
    - 'search' - if current url has as=s
    - 'inproduct' - if current url has as=u
    - actual referrer URL - if none of the above
    */
  if (urlParams.as === 's') {
    return 'search';
  } else if (urlParams.as === 'u') {
    return 'inproduct';
  } else {
    return document.referrer;
  }
};

export const getSearchQuery = function (urlParams, referrer) {
  // If the referrer is a search page, return the search keywords.
  if (referrer === 'search') {
    return urlParams.s;
  } else if (referrer !== 'inproduct') {
    return getQueryParamsAsDict(referrer).q || '';
  }
  return '';
};

export const unquote = function (str) {
  if (str) {
    // Replace all \" with "
    str = str.replace(/\\\"/g, '"');
    // If a string is wrapped in double quotes, remove them.
    if (str[0] === '"' && str[str.length - 1] === '"') {
      return str.slice(1, str.length - 1);
    }
  }
  return str;
};

var UNSAFE_CHARS = {
  '&': '&amp;',
  '<': '&lt;',
  '>': '&gt;',
  "'": '&#39;',
  '"': '&quot;'
};
export const safeString = function (str) {
  if (str) {
    return str.replace(new RegExp('[&<>\'"]', 'g'),
      function (m) { return UNSAFE_CHARS[m]; });
  }
  return str;
};

export const safeInterpolate = function (fmt, obj, named) {
  if (named) {
    for (var j in obj) {
      obj[j] = safeString(obj[j]);
    }
  } else {
    for (var i = 0, l = obj.length; i < l; i++) {
      obj[i] = safeString(obj[i]);
    }
  }
  return interpolate(fmt, obj, named);
};


function onReady() {
  layoutTweaks();
  /* Focus form field when clicking on error message. */
  document.querySelectorAll('#content ul.errorlist a').forEach(function (link) {
    link.addEventListener('click', function (ev) {
      ev.preventDefault();
      var target = document.querySelector(link.getAttribute('href'));
      if (target) {
        target.focus();
      }
    });
  });

  if (document.body.dataset.readonly === 'true') {
    document.querySelectorAll('form[method=post]').forEach(function (form) {
      form.querySelectorAll('input, button, select, textarea').forEach(function (el) {
        el.setAttribute('disabled', 'disabled');
      });
      form.querySelectorAll('input[type=image]').forEach(function (el) {
        el.style.opacity = 0.5;
      });
    });
    document.querySelectorAll('div.editor-tools').forEach(function (el) {
      el.remove();
    });
  }

  initAutoSubmitSelects();
  disableFormsOnSubmit();
  removeAuthToken();
  userMessageUI();

  /* Skip to search (a11y) */
  var skip = document.getElementById('skip-to-search');
  if (skip) {
    skip.addEventListener('click', function (ev) {
      ev.preventDefault();
      var qInputs = document.querySelectorAll('input[name=q]');
      if (qInputs.length) {
        qInputs[qInputs.length - 1].focus();
      }
    });
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', onReady);
} else {
  onReady();
}

window.addEventListener('popstate', function () {
  setTimeout(layoutTweaks, 0);
});

/*
  * Initialize some selects so that they auto-submit on change.
  */
export function initAutoSubmitSelects() {
  document.querySelectorAll('select.autosubmit').forEach(function (select) {
    var submitForm = function () {
      var form = select.closest('form');
      if (form) {
        form.requestSubmit();
      }
    };
    select.addEventListener('change', submitForm);
    select.addEventListener('keyup', submitForm);
  });
}

/*
  * Disable forms on submit to avoid multiple POSTs when double+ clicking.
  * Adds `disabled` CSS class to the form for optionally styling elements.
  *
  * NOTE: We can't disable the buttons because it prevents their name/value
  * from being submitted and we depend on those in some views.
  *
  */
function disableFormsOnSubmit() {
  document.querySelectorAll('form').forEach(function (form) {
    form.addEventListener('submit', function (ev) {
      // Only guard POST forms; default to GET if not specified.
      var method = (form.getAttribute('method') || 'get').toLowerCase();
      if (method !== 'post') {
        return;
      }

      // The `disabled` class doubles as the "already submitting" flag.
      if (form.classList.contains('disabled')) {
        ev.preventDefault();
        return;
      }
      form.classList.add('disabled');

      function enableForm() {
        form.classList.remove('disabled');
      }

      // Re-enable after an async completion (upload/gallery dispatch a native
      // 'ajaxComplete' event on their forms), when the user leaves the page in
      // case they come back, and after 5 seconds as a failsafe.
      form.addEventListener('ajaxComplete', enableForm, { once: true });
      window.addEventListener('unload', enableForm);
      setTimeout(enableForm, 5000);
    });
  });
}

/*
  * Remove an item from a list if it matches the substring match_against.
  * Caution: modifies from_list.
  * E.g. list = ['string'], remove_item(list, 'str') => list is [].
  */
function remove_item(from_list, match_against) {
  match_against = match_against.toLowerCase();
  for (var i in from_list) {
    if (match_against.indexOf(from_list[i]) >= 0) {
      from_list.splice(i, 1);
    }
  }
}

export function userMessageUI() {
  // Add a close button to all messages.
  document.querySelectorAll('.user-messages > li').forEach(function (msg) {
    var closeButton = document.createElement('div');
    closeButton.className = 'close-button';
    msg.appendChild(closeButton);
  });

  function key(msg) {
    return 'user-message::dismissed::' + msg.getAttribute('id');
  }

  // Some messages can be dismissed permanently.
  document.querySelectorAll('.user-messages .dismissible').forEach(function (msg) {
    if (!localStorage.getItem(key(msg))) {
      msg.style.display = '';
    }
  });
  document.querySelectorAll('.user-messages').forEach(function (container) {
    container.addEventListener('click', function (e) {
      var dismiss = e.target.closest('.dismissible .dismiss');
      if (!dismiss) {
        return;
      }
      var msg = dismiss.parentNode;
      localStorage.setItem(key(msg), true);
      msg.style.display = 'none';
    });
  });
}

function layoutTweaks() {
  // Adjust the height of cards to be consistent within a group.
  document.querySelectorAll('.card-grid').forEach(function (grid) {
    var cards = Array.from(grid.children).filter(function (el) {
      return el.tagName === 'LI';
    });
    var max = 0;
    cards.forEach(function (card) {
      var h = card.offsetHeight;
      if (h > max) {
        max = h;
      }
    });
    cards.forEach(function (card) {
      card.style.height = max + 'px';
    });
  });
}

function pad(str, length, padChar) {
  str = '' + str;
  while (str.length < length) {
    str = padChar + str;
  }
  return str;
}

export const dateFormat = function (format, d) {
  var dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday',
    'Friday', 'Saturday'];

  var month = pad(d.getMonth() + 1, 2, '0');
  var date = pad(d.getDate(), 2, '0');
  var hours = pad(d.getHours(), 2, '0');
  var minutes = pad(d.getMinutes(), 2, '0');
  var seconds = pad(d.getSeconds(), 2, '0');

  return interpolate(format, {
    'year': d.getFullYear(),
    'month': month,
    'date': date,
    'day': dayNames[d.getDay()],
    'hours': hours,
    'minutes': minutes,
    'seconds': seconds
  }, true);
};

/* If an auth token is found in the url, remove it. It makes our
  * urls look ugly.
  */
function removeAuthToken() {
  var qs = window.location.search.slice(1);
  var query = qs.split('&').map(function (pair) {
    return [
      pair.split('=')[0],
      pair.split('=').slice(1).join('=')
    ];
  });
  var authFound = false;
  query = query.filter(function (pair) {
    if (pair[0] === 'auth') {
      authFound = true;
      return false;
    }
    return true;
  });

  if (authFound) {
    qs = '?' + query.map(function (pair) { return pair.join('='); }).join('&');
    history.replaceState(this.state, {}, qs);
  }
}
