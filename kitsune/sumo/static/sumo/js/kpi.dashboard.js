/* globals $:false, gettext:false, k:false */
(function() {

'use strict';

function init() {
  makeKPIGraph($('#kpi-questions'), true, [
    {
      name: gettext('Questions'),
      slug: 'questions',
      func: k.Graph.identity('questions'),
      color: '#5d84b2',
      axisGroup: 'questions',
      area: true
    },
    {
      name: gettext('Solved'),
      slug: 'num_solved',
      func: k.Graph.identity('solved'),
      color: '#aa4643',
      axisGroup: 'questions',
      area: true
    },
    {
      name: gettext('% Solved'),
      slug: 'solved',
      func: k.Graph.fraction('solved', 'questions'),
      color: '#aa4643',
      axisGroup: 'percent',
      type: 'percent'
    },
    {
      name: gettext('Responded in 24 hours'),
      slug: 'num_responded_24',
      func: k.Graph.identity('responded_24'),
      color: '#89a54e',
      axisGroup: 'questions',
      area: true
    },
    {
      name: gettext('% Responded in 24 hours'),
      slug: 'responded_24',
      func: k.Graph.fraction('responded_24', 'questions'),
      color: '#89a54e',
      axisGroup: 'percent',
      type: 'percent'
    },
    {
      name: gettext('Responded in 72 hours'),
      slug: 'num_responded_72',
      func: k.Graph.identity('responded_72'),
      color: '#80699b',
      axisGroup: 'questions',
      area: true
    },
    {
      name: gettext('% Responded in 72 hours'),
      slug: 'responded_72',
      func: k.Graph.fraction('responded_72', 'questions'),
      color: '#80699b',
      axisGroup: 'percent',
      type: 'percent'
    },
    {
      name: gettext('Not responded in 24 hours'),
      slug: 'not_responded_24',
      color: '#C98531',
      func: k.Graph.difference('questions', 'responded_24'),
      area: true
    },
    {
      name: gettext('Not responded in 72 hours'),
      slug: 'not_responded_72',
      color: '#DB75C2',
      func: k.Graph.difference('questions', 'responded_72'),
      area: true
    }
  ]);

  makeKPIGraph($('#kpi-vote'), true, [
    {
      name: gettext('Article Votes: % Helpful'),
      slug: 'wiki_percent',
      func: k.Graph.fraction('kb_helpful', 'kb_votes'),
      type: 'percent'
    },
    {
      name: gettext('Answer Votes: % Helpful'),
      slug: 'ans_percent',
      func: k.Graph.fraction('ans_helpful', 'ans_votes'),
      type: 'percent'
    }
  ]);

  makeKPIGraph($('#kpi-active-contributors'), false, [
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

  makeKPIGraph($('#kpi-ctr'), true, [
    {
      name: gettext('Click Through Rate %'),
      slug: 'ctr',
      func: k.Graph.fraction('clicks', 'searches'),
      type: 'percent'
    }
  ]);

  makeKPIGraph($('#kpi-visitors'), true, [
    {
      name: gettext('Visitors'),
      slug: 'visitors',
      func: k.Graph.identity('visitors')
    }
  ]);

  makeKPIGraph($('#kpi-l10n'), true, [
    {
      name: gettext('L10n Coverage'),
      slug: 'l10n',
      // the api returns 0 to 100, we want 0.0 to 1.0.
      func: function(d) { return d.coverage / 100; },
      type: 'percent'
    }
  ]);

  makeKPIGraph($('#exit-survey'), true, [
    {
      name: gettext('Percent Yes'),
      slug: 'percent_yes',
      func: k.Graph.percentage('yes', 'no', 'dont_know'),
      axisGroup: 'percent',
      type: 'percent'
    },
    {
      name: gettext('Yes'),
      slug: 'yes',
      func: k.Graph.identity('yes'),
      axisGroup: 'response'
    },
    {
      name: gettext('No'),
      slug: 'no',
      func: k.Graph.identity('no'),
      axisGroup: 'response'
    },
    {
      name: gettext("I don't know"),
      slug: 'dont_know',
      func: k.Graph.identity('dont_know'),
      axisGroup: 'response'
    }
  ]);

}

function makeKPIGraph($container, bucket, descriptors) {
  $.getJSON($container.data('url'), function(data) {
    new k.Graph($container, {
      data: {
        datums: data.objects,
        seriesSpec: descriptors
      },
      options: {
        legend: 'mini',
        slider: true,
        bucket: bucket
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
