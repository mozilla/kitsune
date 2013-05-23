(function() {

"use strict";

function init() {
  makeKPIGraph($('#kpi-questions'), [
    {
      name: gettext('Questions'),
      slug: 'questions',
      func: k.Graph.identity('questions'),
      color: '#5d84b2',
      axisGroup: 'questions'
    },
    {
      name: gettext('% Solved'),
      slug: 'solved',
      func: k.Graph.fraction('solved', 'questions'),
      color: '#aa4643',
      axisGroup: 'percent'
    },
    {
      name: gettext('% Responded in 24 hours'),
      slug: 'responded_24',
      func: k.Graph.fraction('responded_24', 'questions'),
      color: '#89a54e',
      axisGroup: 'percent'
    },
    {
      name: gettext('% Responded in 72 hours'),
      slug: 'responded_72',
      func: k.Graph.fraction('responded_72', 'questions'),
      color: '#80699b',
      axisGroup: 'percent'
    }
  ]);

  makeKPIGraph($('#kpi-vote'), [
    {
      name: gettext('Article Votes: % Helpful'),
      slug: 'wiki_percent',
      func: k.Graph.fraction('kb_helpful', 'kb_votes')
    },
    {
      name: gettext('Answer Votes: % Helpful'),
      slug: 'ans_percent',
      func: k.Graph.fraction('ans_helpful', 'ans_votes')
    }
  ]);

  makeKPIGraph($('#kpi-active-contributors'), [
    {
      name: gettext('en-US KB'),
      slug: 'en_us',
      func: k.Graph.identity('en_us')
    },
    {
      name: gettext('non en-US KB'),
      slug: 'non_en_us',
      func: k.Graph.identity('non_en_us')
    },
    {
      name: gettext('Support Forum'),
      slug: 'support_forum',
      func: k.Graph.identity('support_forum')
    },
    {
      name: gettext('Army of Awesome'),
      slug: 'aoa',
      func: k.Graph.identity('aoa')
    }
  ]);

  makeKPIGraph($('#kpi-ctr'), [
    {
      name: gettext('Click Through Rate %'),
      slug: 'ctr',
      func: k.Graph.fraction('clicks', 'searches')
    }
  ]);

  makeKPIGraph($('#kpi-visitors'), [
    {
      name: gettext('Visitors'),
      slug: 'visitors',
      func: k.Graph.identity('visitors')
    }
  ]);

  makeKPIGraph($('#kpi-l10n'), [
    {
      name: gettext('L10n Coverage'),
      slug: 'l10n',
      // the api returns 0 to 100, we want 0.0 to 1.0.
      func: function(d) { return d['coverage'] / 100; }
    }
  ]);

}

function makeKPIGraph($container, descriptors) {
  $.getJSON($container.data('url'), function(data) {
    new k.Graph($container, {
      data: {
        datums: data.objects,
        seriesSpec: descriptors
      },
      options: {
        legend: 'mini',
        slider: true,
        bucket: true
      },
      graph: {
        width: 880,
        height: 300
      },
    }).render();
  });
}

$(init);

})();