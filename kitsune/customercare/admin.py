from django.contrib import admin

from kitsune.customercare.models import Tweet, Reply


class TweetAdmin(admin.ModelAdmin):
    date_hierarchy = 'created'
    list_display = ('tweet_id', '__unicode__', 'created', 'locale')
    list_filter = ('locale', 'hidden')
    search_fields = ('raw_json',)
    raw_id_fields = ('reply_to',)

admin.site.register(Tweet, TweetAdmin)


class ReplyAdmin(admin.ModelAdmin):
    date_hierarchy = 'created'
    list_display = ('tweet_id', 'user', 'twitter_username', '__unicode__',
                    'created', 'locale')
    list_filter = ('locale', 'twitter_username')
    search_fields = ('raw_json',)
    raw_id_fields = ('user',)

admin.site.register(Reply, ReplyAdmin)
