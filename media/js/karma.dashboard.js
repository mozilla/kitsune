/*
 * Karma Dashboard backbonejs app.
 */

(function($) {

"use strict";

window.User = Backbone.Model.extend({
    defaults: {
        'selected': false
    }
});

window.Users = Backbone.Collection.extend({
    model: User,
    initialize: function(models, options) {
        this.baseUrl = options.baseUrl;
    },
    url: function() {
        return this.baseUrl;
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
        }
        return users;
    }
});

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

    events: {},

    initialize: function() {
        _.bindAll(this, 'render', 'renderUser');

        this.collection.bind('reset', this.render);
        this.collection.bind('add', this.renderUser);
    },

    render: function() {
        $(this.el).html(this.template({}));
        this.collection.each(this.renderUser);
        return this;
    },

    renderUser: function(user) {
        var view = new UserView({
            model: user
        });
        this.$('tbody').append(view.render().el);
    }
});

window.KarmaDashboard = Backbone.View.extend({
    initialize: function() {
        // Create Users collection.
        window.users = new Users([], {
            baseUrl: $(this.el).data('userlist-url')
        });

        // Create the views.
        this.userListView = new UserListView({
            collection: window.users
        });

        // Render the views.
        $(this.el).append(this.userListView.render().el);

        // Load up the collection.
        users.fetch();
    }
});

// Kick off the application
window.App = new KarmaDashboard({
    el: document.getElementById('karma-dash')
});


}(jQuery));
