from django.contrib.flatpages.models import FlatPage
from django.shortcuts import render_to_response,render
from django.contrib.auth import login,authenticate
from django.contrib.auth.decorators import login_required
from django.forms.models import model_to_dict
from django.template import RequestContext, loader
from django.http import HttpResponse
from django.core.context_processors import csrf
import string, random
import praw
from forms import *
from models import *
from actions import mr
# Create your views here.
def search(request):
    query=request.GET.get('q','')
    results = []
    return render_to_response('fred/fred.html',
                              {'query':query,
                               'results':FlatPage.objects.filter(content__icontains=query)})
def passwordmaker(size=6, chars=string.ascii_uppercase + string.digits+string.ascii_lowercase):
    return ''.join(random.choice(chars) for _ in range(size))

def betterboard(request):
    top = Leaderboard.objects.order_by('-count')
    template = loader.get_template('fred/leaderboard.html')
    context = RequestContext(request, {
        'leaders': top,
    })
    return HttpResponse(template.render(context))

def sub_settings(request):
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = Settings(request.POST)
        # check whether it's valid:
        if form.is_valid():
            form.save()
            # process the data in form.cleaned_data as required
            # ...
            # redirect to a new URL:
            return HttpResponseRedirect('/thanks/')

    # if a GET (or any other method) we'll create a blank form
    else:
        form = Settings()

    return render(request, 'fred/settings.html', {'form': form})

def set_settings(request,sub='helloneighbor'):
    subreddit = Subreddit.objects.get(name=sub)
    subsettings = SubredditSettings.objects.get(name=subreddit)
    d = dict(name=subsettings.name, commentreplytext=subsettings.commentreplytext,replywithpm=subsettings.replywithpm)
    d.update(csrf(request))
    return render_to_response("fred/settings.html",d)

def passwordreset(request):
    if request.method == 'POST':
        p=request.POST
        if p.has_key('username'):
            print p['username']
            newpass = passwordmaker(8)
            person,nothing=User.objects.get_or_create(defaults={'username':p['username']},username__iexact=p['username'])
            person.set_password(newpass)
            person.save()
            mr.send_message(p['username'],'Your password has been reset','Your password for MrRogersBot configuration has been reset. Your new password is '+newpass)
            print newpass
            return HttpResponse('Your password has been reset. Check your reddit mail.<br><a href="/login/">Try again</a>')
        else:
            return HttpResponse('invalid username')

@login_required(login_url='/login/')
def change_settings(request,subname):
    print subname + ' before post'
    # if this is a POST request we need to process the form data
    sub,nothing = Subreddit.objects.get_or_create(defaults={'name':subname},name__iexact=subname)
    data,nothing = SubSettings.objects.get_or_create(defaults={'name':sub},name=sub)
    moderator, nothing = User.objects.get_or_create(defaults={'username':request.user.username},username__iexact=request.user.username)
    #try:
    if 1:
        if 'aaron' == str(moderator) or str(moderator)=='noeatnosleep'or mr.get_redditor(request.user.username) in mr.get_subreddit(subname).get_moderators():
            if request.method == 'POST':
                p=request.POST
                print data.name
                print subname +' after post'
                if p.has_key('replywithcomment'):
                    data.replywithcomment=p['replywithcomment']
                if p.has_key('replywithpm'):
                    data.replywithpm=p['replywithpm']
                data.pmreplytext=p['pmreplytext']
                data.pmreplytitle=p['pmreplytitle']
                data.commentreplytext=p['commentreplytext']
                data.usebuiltinreasons=p.get('usebuiltinreasons',False)
                data.ignoreunmappedreasons=p.get('ignoreunmappedreasons',False)
                print 'saving changes'
                print data.__dict__
                data.save()
                change = ChangeLog(sub=sub,mod=moderator)
                change.save()
                form = SettingsForm(initial=model_to_dict(data))        # create a form instance and populate it with data from the request:
            # if a GET (or any other method) we'll create a blank form
            else:
                form = SettingsForm(initial=model_to_dict(data))
                form.subreddit = subname
        else:
            return HttpResponse('You are not a moderator of /r/'+subname+ ", or /u/MrRogersbot isn't a moderator there")
    #except:
    #    return HttpResponse('not a valid user')

    return render(request, 'fred/settings.html', {'form': form})

def logon(request):
    username = request.POST['username']
    password = request.POST['password']
    user = authenticate(username=username, password=password)
    if user is not None:
        login(request, user)