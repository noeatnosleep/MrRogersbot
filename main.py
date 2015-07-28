# -*- coding: utf-8 -*-
import praw
import bayes
import os

#Connect to django database
from Neighborhood.Neighborhood import settings as s
dbs = s.DATABASES
from django.conf import settings
settings.configure(DATABASES=dbs)
name = __name__ #next part messes up __name__
for dirs in os.walk('Neighborhood').next()[1]:
    #import all the models from apps in the django application. This is pretty ugly and should be done differently.
    try: #really only fred.models is used
        models = (__import__('Neighborhood.'+dirs+'.models', globals(), locals(), ['*']))
        for k in dir(models):
            locals()[k] = getattr(models, k) #load everything from all the modules in the Neighborhood directory as local variables
    except:
        print 'failed to import'
import django
django.setup()

__name__ = name #put back __name__
subsettings = {}
from accounts import users  # userid and password are in another file for security

already_done = set()  # list of comments that have already been processed. processing it twice doesn't break anything.
reasonsmap = {'spam':'spam','Spam':'spam','vote manipulation':'troll','personal information':'toxic','toxic':'toxic','removed spam':'spam','abuse':'toxic','abusive':'toxic','Toxic':'toxic'}
types = ['spam', 'troll', 'toxic']


def check_queue_and_modlog(mod):#check modqueue for comments to add to bad corpus
    for comment in mod.get_mod_queue('mod'):#get the mod queue, cycle through items
        if "Comment" in str(comment.__class__):#is the item a comment?
            if comment.mod_reports:#does the item have moderator reports?
                reportmod = comment.mod_reports[0][1]#moderator name from report
                if comment.id not in already_done and 'MrRogersbot' not in reportmod and 'AutoModerator' not in reportmod: #ignore comments that have already been looked at, and comments reported by the bot an AM
                    reason = comment.mod_reports[0][0]#report reason
                    text = comment.body.encode('ascii', 'ignore') #get the comment text
                    if ignorecomment(str(comment.subreddit),reason) == False: #check to see if the report reason is logged for this subreddit
                        try:
                            reason = reasonsmap[reason] #convert default report reasons to custom ones
                        except KeyError: #if "other" reason not in the conversion table
                            print "Report reason not found: " + str(comment.mod_reports[0][0])
                            reason = 'other'
                        logremoval(reportmod,comment,reason,mod) #log the mod report to the database
                        addtocorpus(reason, text, comment.id) #add the comment text to the appropriate corpus
                        handle_comment(comment,mod) #remove the comment
    #check mod log for comments to add to corpus
    for comment in mod.get_mod_log('mod',mod=None,action='approvecomment'):  # approved comments are ham
        if comment.id not in already_done: #only add to the ham corpus once
            already_done.add(comment.id)
            try:
                print "logging approved comment"
                target = mod.get_submission(url='http://www.reddit.com/'+comment.target_permalink).comments[0] #get the comment text
                text = target.body.encode('ascii', 'ignore') #convert to ascii
                addtocorpus('ham', text, target.id) #add to the ham corpus
            except:
                pass
    for comment in mod.get_mod_log('mod',mod=None,action='removecomment'):
    #comments removed by automoderator are either spam or maybe bad from a rule
        if str(comment.mod) == 'AutoModerator':
            if comment.id not in already_done:
                already_done.add(comment.id)
                try:
                    commentsettings = subsettings[(str(comment.subreddit))] #see if automod removal reason is mapped to a report reason
                    if commentsettings['useamremovals'] == True: #ability to ignore comments removed by AM on a sub by sub basis
                        print 'adding automoderator removed comment'
                        target = mod.get_submission(url='http://www.reddit.com/'+comment.target_permalink).comments[0] #get comment text
                        text = target.body.encode('ascii', 'ignore') #convert to ascii
                        if comment.details in types: #see if there's a removal reason that maps to a known reason
                            reason = reasonsmap[comment.details] #get the reason
                            addtocorpus(reason, text, target.id) #add to the appropriate corpus
                        else:
                            addtocorpus('automod', text, target.id) #otherwise, add to generic automoderator corpus
                except:
                    pass

def logremoval(user,comment,reportreason,mod): # add the report and removal to the log and update the leaderboard
    user = mod.get_redditor(user)
    person,nothing = People.objects.get_or_create(redditid=user.id,username=user.name) #get person from database or create
    print person
    person.save()
    log,nothing = Leaderboard.objects.get_or_create(redditid=person) #get the leaderboard entry for the mod who reported comment
    log.count += 1 #increment leaderboard
    log.save()
    removal, nothing = ReportLog.objects.get_or_create(mod = person, commentid = comment.id, reason = reportreason)#log removal to reportlog
    removal.save()

def addtocorpus(reason,text,id):
    with open("corpus/"+reason+'/'+id+'.txt', "w") as text_file:
         text_file.write(text) #adds a comment to the corpus with correct tag

#check new comments against database:
def check_new_comments(mod):
    for comment in mod.get_comments('mod'):
            if comment.id not in already_done:
                already_done.add(comment.id)
                test_comment(comment)

def handle_comment(comment,moderator): #do stuff to a comment based on settings
    try: #try to get subreddit settings from the database
        commentsettings = subsettings[(str(comment.subreddit))] #sometimes this doesn't work for some reason
        if commentsettings['replywithpm'] == True: #reply to the removal with a PM
            moderator.send_message(str(comment.author),commentsettings['pmreplytitle'],commentsettings['pmreplytext'])
        if commentsettings['replywithcomment'] == True: #reply to the removal with a comment
            comment.reply(commentsettings['commentreplytext'])
    except KeyError: #if there are no subreddit settings in the database, don't leave any response
        pass
    comment.remove(spam=False) #remove the reported comment
    subtext = '' #this isn't used. the rest of this function can be ignored.
    if subtext:
        comment.reply(subtext)
    title = "I'd like to talk to you for a minute"
    text = '''Hello Neighbor.

I see you commented [here](%s) and I want to thank you for contributing your thoughts to the discussion with your Internet neighbors happening all over the world.

I'd like you to take a minute and reread your comment. Sometimes when you're in a discussion and can't see the person you're talking with, you might say things that you would not say to someone face-to-face.

I believe in you, and I know that what you have to say is worth hearing.

“There are three ways to ultimate success: The first way is to be kind. The second way is to be kind. The third way is to be kind.” - Fred Rogers

Thank you for taking the time to read this.''' % str(comment.link_url)


def ignorecomment(subreddit,reason): #see if a reported comment should be ignored. Used for subs who use moderator reports like /r/science
    try:
        commentsettings = subsettings[(str(subreddit))] #try to get subreddit settings from database
    except KeyError: #default setting is to add all reported comments to corpus
        return False
    if commentsettings['usebuiltinreasons'] == True: #map the builtin reasons to custom reasons
        try:
            reasons = reasonsmap[reason]
        except KeyError:
            if commentsettings['ignoreunmappedreasons'] == True: #for subs that use 'other' mod report reasons.
                return True     # Only remove and log comments with report reasons that match mapped reasons
            else:
                return False
    else:
        if commentsettings['ignoreunmappedreasons'] == True:
            if reason not in ['spam','troll','toxic']:
                return False
            else:
                return True

def reportstuff(moderator):
    pass


def reload_db():
    bayes.load_classifier()

def rebuild_db():
    bayes.train_all(None,'corpus')

def test_comment(comment):
    result = bayes.test_comment(comment.body)

def check_mail(mod): #look for moderator invites
        for message in mod.get_unread():
            if message.was_comment:
                continue
            # if it's a subreddit invite
            if not message.author and message.subject.startswith('invitation to moderate /r/'):
                message.mark_as_read()
                accept_invite(message,mod) #accept the invite and send a welcome modmail


def accept_invite(message,mod): #accept moderator invite
    default_config = ''' '''
    if message.id not in already_done:
        already_done.add(message.id) #this isn't strictly necessary because it only gets unread messages and marks the messages read
        print "accepting moderator invite to " +message.subreddit.display_name.lower()
        mod.accept_moderator_invite(message.subreddit.display_name.lower()) #accept the invite
        welcometopic = 'Thank you for inviting me to your subreddit.'
        welcometext = '''Here are some links about [what this bot does](https://www.reddit.com/r/HelloNeighbor/wiki/intro) and [how to use it](https://www.reddit.com/r/HelloNeighbor/wiki/howtouse).

The tldr is that instead of removing comments, you should report them instead. Use the 'spam' reason for spam comments, and type 'toxic' in the 'other' field for toxic or hateful comments. I learn from the comments that you approve and the ones you report.

I don't yet have a large enough sample size of good and bad comments to start making suggestions, so I need your help and input.

Let me know if you have any questions, or make a post on /r/helloneighbor.'''
        mod.send_message(message.subreddit,welcometopic, welcometext) #send welcome message

def getsettings(): #reload subreddit settings from the database
    for sub in SubSettings.objects.all():
        subsettings[str(sub).lower()]=sub.__dict__


def cycle():
    getsettings() #reload subreddit settings from database
    for mod in users:
        check_queue_and_modlog(mod) #check modqueue and log for each user account


def ignoreoldlog(mod): #makes the bot load faster
    print 'ignoring old comments in the log'
    for comment in mod.get_mod_log('mod',mod=None,action='approvecomment'):
        already_done.add(comment.id)
    #for comment in nens.get_mod_log('mod',mod=None,action='removecomment'):
    #    if comment.mod == 'Automoderator':
    #        already_done.add(comment.id)
    #for comment in mr.get_mod_log('mod',mod=None,action='removecomment'):
    #    if comment.mod == 'Automoderator':
    #        already_done.add(comment.id)
    print 'done'


def deleteme(): #was used for adding old AM removals to corpus
    for sub in mr.get_my_moderation():
        try:
            commentsettings = subsettings[(str(sub))]
            if commentsettings['useamremovals'] == True:
                for comment in mr.get_mod_log(sub,mod='AutoModerator',action='removecomment',limit=None):
                    if str(comment.mod) == 'AutoModerator':
                        print 'automod',str(sub)
                        if comment.id not in already_done:
                            already_done.add(comment.id)
                            try:
                                if commentsettings['useamremovals'] == True:
                                    print 'adding automoderator removed comment'
                                    target = mr.get_submission(url='http://www.reddit.com/'+comment.target_permalink).comments[0]
                                    text = target.body.encode('ascii', 'ignore')
                                    if comment.details in types:
                                        reason = reasonsmap[comment.details]
                                        addtocorpus(reason, text, target.id)
                                    else:
                                        addtocorpus('automod', text, target.id)
                            except:
                                pass
        except:
            pass

if __name__ == '__main__':
    for mod in users:
        ignoreoldlog(mod)
    print 'begin checking queue'
    while 1:
        while 1: #turn this on for debug
        #try: #turn off for debug
            cycle()
            check_mail(users[0])
        ##except Exception as e: #turn off for debug
         #   print str(e) #turn off for debug. needs to show more traceback information.
