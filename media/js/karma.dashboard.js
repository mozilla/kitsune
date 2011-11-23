/*
 * Karma Dashboard backbonejs app.
 */

(function($) {

"use strict";

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
    initialize: function(models, options) {
        _.bindAll(this, 'settingsChanged');

        this.settings = options.settings;
        this.page = 1;

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
        var url = this.settings.get('baseUsersUrl') + '?' + $.param({
           sort: this.settings.get('sort'),
           daterange: this.settings.get('daterange'),
           pagesize: this.settings.get('pagesize'),
           page: this.page
        });
        return url;
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

            // TODO: calculate and add aggregate properties (%s for bkg vis).
        }
        return users;
    },
    fetchMore: function() {
        this.page++;
        this.fetch({add: true});
    },
    settingsChanged: function() {
        this.fetch();
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


/*
 * Application
 */
window.KarmaDashboard = Backbone.View.extend({
    initialize: function() {
        // Create models and collections.
        window.settings = new Settings();
        settings.fetch();
        settings.save({
            baseUsersUrl: $(this.el).data('userlist-url')
        });

        window.users = new Users([], {
            settings: settings
        });

        // Create the views.
        this.dateRangeView = new DateRangeView({
            settings: settings
        });
        this.userListView = new UserListView({
            collection: window.users,
            settings: settings
        });

        // Render the views.
        $(this.el)
            .append(this.dateRangeView.render().el)
            .append(this.userListView.render().el);

        // Load up the collection.
        users.fetch();
    }
});

// Kick off the application
window.App = new KarmaDashboard({
    el: document.getElementById('karma-dash')
});


}(jQuery));
