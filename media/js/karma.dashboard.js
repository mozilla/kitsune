/*
 * Bar charts
 */

function deslugify(slug){
    return _.map(slug.split('-'), function(w) {
        return w.charAt(0).toUpperCase() + w.slice(1)
    }).join(' ')
}


/*
 * Karma Dashboard backbonejs app.
 */

(function($) {

"use strict";
var chart1;
/*
 * Models
 */
window.User = Backbone.Model.extend({
    defaults: {
        'selected': false
    }
});

window.Users = Backbone.Collection.extend({
    model: User,
    valueProperties: ['points', 'answer', 'firstanswer', 'solution',
                      'helpfulanswer', 'nothelpfulanswer'],
    initialize: function(models, options) {
        _.bindAll(this, 'settingsChanged');
        this.settings = options.settings;
        this.page = 1;
        this.max = {};

        this.settings.bind('change', this.settingsChanged);
    },
    fetch: function(options) {
        var result,
            fresh = !options || !options.add;
        if (fresh) {
            // Reset the page to 1 if this is a fresh fetch.
            this.page = 1;
        }
        return Backbone.Collection.prototype.fetch.call(this, options);
    },
    url: function() {
        return this.settings.get('baseUsersUrl') + '?' + $.param({
           sort: this.settings.get('sort'),
           daterange: this.settings.get('daterange'),
           pagesize: this.settings.get('pagesize'),
           page: this.page
        });
    },
    parse: function(response) {
        var users = [],
            tmpUser;
        if (response && response.success) {
            _.each(response.results, function(result) {
                tmpUser = {};
                _.each(response.schema, function(key, i) {
                    tmpUser[key.replace(/-/g, '')] = result[i];
                });
                users.push(tmpUser);
            });

            // When fetching a fresh collection, recalculate the maxes.
            if (this.page === 1) {
                this.resetMax();
                _.each(users, function(user) {
                    _.each(this.valueProperties, function(key) {
                        if (user[key] > this.max[key]) {
                            this.max[key] = user[key];
                        }
                    }, this);
                }, this);
                // Make helpful max = not helpful max.
                this.max['helpfulanswer'] = this.max['nothelpfulanswer'] =
                    _.max([this.max['helpfulanswer'], this.max['nothelpfulanswer']]);
            }

            // Calculate property values as a % of max.
            _.each(users, function(user) {
                _.each(this.valueProperties, function(key) {
                    user[key + 'Perc'] =
                        Math.round(user[key]*100/this.max[key]);
                }, this);
            }, this);

            // TODO: We are looping over 100 (or pageSize) users 2-3 times.
            // Maybe optimize.
        }
        return users;
    },
    fetchMore: function() {
        this.page++;
        this.fetch({add: true});
    },
    settingsChanged: function() {
        this.fetch();
    },
    resetMax: function() {
        _.each(this.valueProperties, function(key) {
            this.max[key] = 0;
        }, this);
    }
});

window.Settings = Backbone.Model.extend({
    defaults: {
        sort: 'points',
        daterange: '1y',
        pagesize: 100
    },
    sync: function(method, model, options) {
        // Use localStorage to persist settings.
        var resp,
            key = 'settings';
        if (method === 'read') {
            resp = JSON.parse(localStorage.getItem(key));
        } else if (method === 'create' || method === 'update') {
            resp = localStorage.setItem(key, JSON.stringify(model));
        } else if (method == 'delete') {
            resp = localStorage.removeItem(key);
        }
        resp ? options.success(resp) : options.error('Record not found');
    }
});

window.Overview = Backbone.Model.extend({
    defaults: {
        'question': 0,
        'firstanswer': 0,
        'solution': 0,
        'answer': 0,
        'helpfulanswer': 0,
        'nothelpfulanswer': 0
    },

    initialize: function(models, options) {
        _.bindAll(this, 'settingsChanged');
        this.settings = options.settings;

        this.settings.bind('change:daterange', this.settingsChanged);
    },
    url: function() {
        return this.settings.get('overviewUrl') + '?' + $.param({
           daterange: this.settings.get('daterange')
        });
    },
    parse: function(response) {
        var clean = {};
        _.each(response.overview, function(val, key) {
            clean[key.replace(/-/g, '')] = val;
        });
        return clean;
    },
    settingsChanged: function() {
        this.fetch();
    }
});

window.ChartModel = Backbone.Model.extend({
    initialize: function(models, options) {
        _.bindAll(this, 'settingsChanged');
        this.settings = options.settings;

        this.settings.bind('change:daterange', this.settingsChanged);
    },
    url: function() {
        return this.settings.get('detailUrl') + '?' + $.param({
           daterange: this.settings.get('daterange')
        });
    },
    settingsChanged: function() {
        this.fetch();
    },
    parse: function(response, options) {
        var i, l = response.time_units.length;
        var data = [];
        var date, day, month, year, weekDay;

        var now = new Date();
        var months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        var days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday',
                    'Thursday', 'Friday', 'Saturday'];
        // graph lines line up nicely.
        var offset = -now.getTimezoneOffset() / 60;

        for (i = 0; i < l; i++) {
            month = months.indexOf(response.time_units[i]);
            year = now.getFullYear();
            if (month === -1) {
                // If it isn't months, it must be days. assume the data
                // is the last 7 days. HACK HACK HACK.
                day = now.getDate() - (6 - i);
                month = now.getMonth();
            } else {
                day = 1;
                if (month > now.getMonth()) {
                    year -= 1;
                }
            }
            date = new Date(year, month, day, offset) / 1000;

            data.push({
                answer: response.counts.answer[i],
                nothelpful: response.counts['nothelpful-answer'][i],
                solution: response.counts.solution[i],
                helpful: response.counts['helpful-answer'][i],
                first: response.counts['first-answer'][i],
                date: date
            });
        }

        return {data: data};
    }
});


/*
 * Views
 */
window.UserView = Backbone.View.extend({
    template: _.template($("#user-template").html()),
    tagName: 'tr',
    className: 'user',

    events: {},

    initialize: function() {
        _.bindAll(this, 'render');
    },

    render: function() {
        $(this.el).html(this.template(this.model.toJSON()));
        return this;
    }
});

window.UserListView = Backbone.View.extend({
    template: _.template($("#userlist-template").html()),
    tagName: 'section',
    className: 'user-list',

    events: {
        'click .sortable:not(.sort)': 'sort'
    },

    initialize: function() {
        _.bindAll(this, 'render', 'renderUser');

        this.settings = this.options.settings;

        this.collection.bind('reset', this.render);
        this.collection.bind('add', this.renderUser);
    },

    render: function() {
        $(this.el).html(this.template({
            sort: this.settings.get('sort')
        }));
        this.collection.each(this.renderUser);
        return this;
    },

    renderUser: function(user) {
        var view = new UserView({
            model: user
        });
        this.$('tbody').append(view.render().el);
    },

    sort: function(e) {
        var sortBy = $.trim(e.target.className.replace('sortable', ''));
        this.settings.save({sort: sortBy});
    }
});

window.DateRangeView = Backbone.View.extend({
    template: _.template($("#daterange-template").html()),
    tagName: 'section',
    className: 'daterange',

    events: {
        'change select': 'updateSettings'
    },

    initialize: function() {
        _.bindAll(this, 'render', 'updateSettings');

        this.settings = this.options.settings;
    },

    render: function() {
        $(this.el).html(this.template({
            daterange: this.settings.get('daterange')
        }));
        return this;
    },

    updateSettings: function() {
        this.settings.save({
            daterange: this.$('select').val()
        });
    }
});

window.OverviewView = Backbone.View.extend({
    template: _.template($("#overview-template").html()),
    tagName: 'section',
    className: 'overview',

    initialize: function() {
        _.bindAll(this, 'render');

        this.model.bind('change', this.render);
    },

    render: function() {
        $(this.el).html(this.template(this.model.toJSON()));
        return this;
    }
});

/*
 * Application
 */
window.KarmaDashboard = Backbone.View.extend({
    initialize: function() {
        // Create models and collections.
        window.settings = new Settings();
        settings.fetch();
        settings.save({
            baseUsersUrl: $(this.el).data('userlist-url'),
            overviewUrl: $(this.el).data('overview-url'),
            detailUrl: $(this.el).data('details-url')
        });

        window.overview = new Overview([], {
            settings: settings
        });

        window.users = new Users([], {
            settings: settings
        });

        window.chart = new ChartModel([], {
            settings: settings
        });

        // Create the views.
        this.dateRangeView = new DateRangeView({
            settings: settings
        });
        this.overviewView = new OverviewView({
            model: overview,
            settings: settings
        });
        this.userListView = new UserListView({
            collection: window.users,
            settings: settings
        });

        // Render the views.
        $(this.el)
            .append(this.dateRangeView.render().el)
            .append(this.overviewView.render().el)
            .append(this.userListView.render().el);

        // Load up the collections and models.
        users.fetch();
        overview.fetch();
        chart.fetch();

        // Infinite scroll.
        var $window = $(window),
            $document = $(document),
            fudgeFactor = 600;
        $window.bind('scroll', _.throttle(function(){
            if ($window.scrollTop() + fudgeFactor >
                $document.height() - $window.height()){
                users.fetchMore();
            }
        }, 300));
    }
});

function makeGraph() {
    var $container = $('#karma-dash');
    var rendered = false;
    var graph = new k.Graph($container.find('.rickshaw'), {
        data: {
            datums: [],
            seriesSpec: [
                {
                    name: gettext('Answers'),
                    func: k.Graph.identity('answer'),
                    color: '#4572A7'
                },
                {
                    name: gettext('Unhelpful Answers'),
                    func: k.Graph.identity('nothelpful'),
                    color: '#AA4643'
                },
                {
                    name: gettext('Solutions'),
                    func: k.Graph.identity('solution'),
                    color: '#89A54E'
                },
                {
                    name: gettext('Helpful Answers'),
                    func: k.Graph.identity('helpful'),
                    color: '#80699B'
                },
                {
                    name: gettext('First Answers'),
                    func: k.Graph.identity('first'),
                    color: '#3D96AE'
                }
            ]
        },
        options: {
            legend: 'mini',
            slider: false,
            bucket: false,
            init: false
        },
        graph: {
            width: 600,
            height: 300,
            renderer: 'bar',
            unstack: true,
            gapSize: 0.2
        }
    });

    chart.bind('change', function() {
        var d;

        graph.data.datums = chart.get('data');

        if (rendered) {
            graph.initData();
            graph.update();
        } else {
            graph.init();
            graph.render();
            rendered = true;
        }
    });
}

// Kick off the application
window.App = new KarmaDashboard({
    el: document.getElementById('karma-dash')
});

makeGraph();

}(jQuery));
