from django.contrib import admin

from customercare.models import Tweet


class TweetAdmin(admin.ModelAdmin):
    date_hierarchy = 'created'
    list_display = ('tweet_id', '__unicode__', 'created', 'locale')
    list_filter = ('locale', 'hidden')
    search_fields = ('raw_json',)
admin.site.register(Tweet, TweetAdmin)
