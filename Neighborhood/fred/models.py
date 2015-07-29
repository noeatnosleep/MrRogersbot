from django.db import models
from django.contrib.flatpages.models import FlatPage
from django.contrib.auth.models import User
# Create your models here.

class SearchKeyword(models.Model):
    keyword=models.CharField(max_length=50)
    page=models.ForeignKey(FlatPage)
    def __unicode__(self): # __str__ for Python 3, __unicode__ for Python 2
        return self.name

class People(models.Model):
    username = models.CharField(max_length=100)
    redditid = models.CharField(max_length=100)
    def __unicode__(self):              # __unicode__ on Python 2
        return self.username

class Leaderboard(models.Model):
    redditid = models.ForeignKey(People)
    count = models.IntegerField(default=0)
    def __unicode__(self):              # __unicode__ on Python 2
        return str(self.redditid)
    def increment(self):
        self.count+=1

class Subreddit(models.Model):
    name = models.CharField(max_length=50)
    moderators = models.ManyToManyField(User)
    def __unicode__(self):              # __unicode__ on Python 2
        return self.name

class ReportLog(models.Model):
    commentid = models.CharField(max_length=20)
    mod = models.ForeignKey(People)
    reason = models.CharField(max_length=200)
    def __unicode__(self):
        return str(self.mod)

class ChangeLog(models.Model):
    change = models.DateTimeField(auto_now_add=True)
    sub = models.ForeignKey(Subreddit)
    mod = models.ForeignKey(User)
    list_display = ('change','sub','mod')
    def __unicode__(self):
        return str(self.change) + " " + str(self.sub)+" "+ str(self.mod)

class SubSettings(models.Model):
    name = models.ForeignKey(Subreddit)
    replywithcomment = models.BooleanField(default=False)
    remove = models.BooleanField(default=False)
    spamthreshold = models.IntegerField(default=100)
    toxicthreshold = models.IntegerField(default=100)
    trollthreshold = models.IntegerField(default=100)
    replywithpm = models.BooleanField(default=False)
    useamremovals=models.BooleanField(default=False)
    usebuiltinreasons = models.BooleanField(default=True)
    ignoreunmappedreasons = models.BooleanField(default=False)
    pmreplytitle = models.CharField(max_length=200,default='removal title')
    pmreplytext = models.TextField(default = 'Your comment was removed. This is the PM')
    commentreplytext = models.TextField(default = 'Comment removed, this is the reply comment')
    def __unicode__(self):
        return str(self.name)