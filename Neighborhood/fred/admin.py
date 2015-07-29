from django.contrib import admin
# Register your models here.
from fred.models import *
admin.site.register(SearchKeyword)

admin.site.register(People)
admin.site.register(Subreddit)
admin.site.register(Leaderboard)
admin.site.register(ReportLog)
admin.site.register(SubSettings)
admin.site.register(ChangeLog)
