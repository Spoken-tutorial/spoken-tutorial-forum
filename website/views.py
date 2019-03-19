import json

from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404
from django.core.context_processors import csrf
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.mail import EmailMultiAlternatives
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth import get_user_model

from website.models import Question, Answer, Notification, AnswerComment
from spoken_auth.models import TutorialDetails, TutorialResources
from website.forms import NewQuestionForm, AnswerQuesitionForm
from website.helpers import get_video_info, prettify
from forums.config import VIDEO_PATH
from website.templatetags.permission_tags import can_edit

# For spam classifier
from OnlySpam import predictorspam
from bs4 import BeautifulSoup
from django.contrib import messages

User = get_user_model()
categories = []
trs = TutorialResources.objects.filter(Q(status=1) | Q(status=2), language__name='English')
trs = trs.values('tutorial_detail__foss__foss').order_by('tutorial_detail__foss__foss')

for tr in trs.values_list('tutorial_detail__foss__foss').distinct():
    categories.append(tr[0])


def home(request):
    questions = Question.objects.filter(status=1).order_by('date_created').reverse()[:10]
    context = {
        'categories': categories,
        'questions': questions
    }
    return render(request, "website/templates/index.html", context)


def questions(request):
    questions = Question.objects.filter(status=1).order_by('date_created').reverse()
    paginator = Paginator(questions, 20)
    page = request.GET.get('page')

    try:
        questions = paginator.page(page)
    except PageNotAnInteger:
        questions = paginator.page(1)
    except EmptyPage:
        questions = paginator.page(paginator.num_pages)
    context = {
        'questions': questions
    }
    return render(request, 'website/templates/questions.html', context)


def question_category(request):
    context = {}
    context['category'] = request.GET.get('category', None)
    context['tutorial'] = request.GET.get('tutorial', None)
    context['minute_range'] = request.GET.get('minute_range', None)
    context['second_range'] = request.GET.get('second_range', None)
    return render(request, 'website/templates/question_category.html', context)


def hidden_questions(request):
    questions = Question.objects.filter(status=0).order_by('date_created').reverse()
    paginator = Paginator(questions, 20)
    page = request.GET.get('page')

    try:
        questions = paginator.page(page)
    except PageNotAnInteger:
        questions = paginator.page(1)
    except EmptyPage:
        questions = paginator.page(paginator.num_pages)
    context = {
        'questions': questions
    }
    return render(request, 'website/templates/questions.html', context)


def get_question(request, question_id=None, pretty_url=None):
    question = get_object_or_404(Question, id=question_id)
    pretty_title = prettify(question.title)
    if pretty_url != pretty_title:
        return HttpResponseRedirect('/question/' + question_id + '/' + pretty_title)
    answers = question.answer_set.all()
    form = AnswerQuesitionForm()
    context = {
        'question': question,
        'answers': answers,
        'form': form
    }
    context.update(csrf(request))
    # updating views count
    question.views += 1
    question.save()
    return render(request, 'website/templates/get-question.html', context)


@login_required
def question_answer(request):

    if request.method == 'POST':
        form = AnswerQuesitionForm(request.POST)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            qid = cleaned_data['question']
            body = cleaned_data['body']
            res = predictorspam(body, False)
            if res == 0:
                messages.success(request, "Our system detects that you are trying to enter a possibly\
                 spam content. Please contact the site admin if you wish to publish the same.")
                return HttpResponseRedirect(request.META['HTTP_REFERER'])

            question = get_object_or_404(Question, id=qid)
            answer = Answer()
            answer.uid = request.user.id
            answer.question = question
            answer.body = body.encode('unicode_escape')
            answer.save()
            if question.uid != request.user.id:
                notification = Notification()
                notification.uid = question.uid
                notification.pid = request.user.id
                notification.qid = qid
                notification.aid = answer.id
                notification.save()

                user = User.objects.get(id=question.uid)
                # Sending email when an answer is posted
                subject = 'Question has been answered'
                message = """
                    Dear {0}<br><br>
                    Your question titled <b>"{1}"</b> has been answered.<br>
                    Link: {2}<br><br>
                    Regards,<br>
                    Spoken Tutorial Forums
                """.format(
                    user.username,
                    question.title,
                    'http://forums.spoken-tutorial.org/question/' + str(question.id) + "#answer" + str(answer.id)
                )

                email = EmailMultiAlternatives(
                    subject, '', 'forums',
                    [user.email],
                    headers={"Content-type": "text/html;charset=iso-8859-1"}
                )

                email.attach_alternative(message, "text/html")
                email.send(fail_silently=True)
                # End of email send
        return HttpResponseRedirect('/question/' + str(qid) + "#answer" + str(answer.id))
    return HttpResponseRedirect('/')


@login_required
def answer_comment(request):
    if request.method == 'POST':
        answer_id = request.POST['answer_id']
        body = request.POST['body']
        answer = get_object_or_404(Answer, pk=answer_id)
        comment = AnswerComment()
        comment.uid = request.user.id
        comment.answer = answer
        comment.body = body.encode('unicode_escape')
        comment.save()

        # notifying the answer owner
        if answer.uid != request.user.id:
            notification = Notification()
            notification.uid = answer.uid
            notification.pid = request.user.id
            notification.qid = answer.question.id
            notification.aid = answer.id
            notification.cid = comment.id
            notification.save()

            user = User.objects.get(id=answer.uid)
            subject = 'Comment for your answer'
            message = """
                Dear {0}<br><br>
                A comment has been posted on your answer.<br>
                Link: {1}<br><br>
                Regards,<br>
                Spoken Tutorial Forums
            """.format(
                user.username,
                "http://forums.spoken-tutorial.org/question/" + str(answer.question.id) + "#answer" + str(answer.id)
            )
            forums_mail(user.email, subject, message)

        # notifying other users in the comment thread
        uids = answer.answercomment_set.filter(answer=answer).values_list('uid', flat=True)
        # getting distinct uids
        uids = set(uids)
        uids.remove(request.user.id)
        for uid in uids:
            notification = Notification()
            notification.uid = uid
            notification.pid = request.user.id
            notification.qid = answer.question.id
            notification.aid = answer.id
            notification.cid = comment.id
            notification.save()

            user = User.objects.get(id=uid)
            subject = 'Comment has a reply'
            message = """
                Dear {0}<br><br>
                A reply has been posted on your comment.<br>
                Link: {1}<br><br>
                Regards,<br>
                Spoken Tutorial Forums
            """.format(
                user.username,
                "http://forums.spoken-tutorial.org/question/" + str(answer.question.id) + "#answer" + str(answer.id)
            )
            forums_mail(user.email, subject, message)
    return HttpResponseRedirect("/question/" + str(answer.question.id) + "#")


def filter(request, category=None, tutorial=None, minute_range=None, second_range=None):
    context = {
        'category': category,
        'tutorial': tutorial,
        'minute_range': minute_range,
        'second_range': second_range
    }

    if category and tutorial and minute_range and second_range:
        questions = Question.objects.filter(category=category).filter(tutorial=tutorial).filter(
            minute_range=minute_range).filter(second_range=second_range, status=1)
    elif tutorial is None:
        questions = Question.objects.filter(category=category, status=1)
    elif minute_range is None:
        questions = Question.objects.filter(category=category).filter(tutorial=tutorial, status=1)
    else:  # second_range is None
        questions = Question.objects.filter(category=category).filter(
            tutorial=tutorial).filter(minute_range=minute_range, status=1)

    if 'qid' in request.GET:
        context['qid'] = int(request.GET['qid'])

    context['questions'] = questions.order_by('category', 'tutorial', 'minute_range', 'second_range')
    return render(request, 'website/templates/filter.html', context)


@login_required
def new_question(request):
    context = {}
    if request.method == 'POST':
        if request.POST['action'] == 'Submit Question':
            content = request.POST['body']
            title = request.POST['title']
            category = request.POST.get('category', None)
            tutorial = request.POST.get('tutorial', None)

            try:
                tutorial_detail_id = \
                    TutorialDetails.objects.filter(tutorial=tutorial).values('foss', 'id')
                path = str(tutorial_detail_id[0]['foss']) + '/' \
                    + str(tutorial_detail_id[0]['id'])
            except BaseException:

                tutorial_detail_id = \
                    TutorialDetails.objects.filter(foss__foss=category).values('foss'
                                                                               )
                path = tutorial_detail_id[0]['foss']
            resultspam = predictorspam(content, path)
            warning = ''
            if resultspam == 0:
                warning = \
                    'Our system detects you have entered a text \
                that is not related to the tutorials directly or is not very clear .\
                Do you want admin to review the same?'
                context['help'] = warning

                context['tut'] = tutorial
                minute_range = request.POST.get('minute_range', None)
                context['minute_range'] = minute_range
                second_range = request.POST.get('second_range', None)
                context['second_range'] = second_range

                # pass minute_range and second_range value to NewQuestionForm to populate on select

                form = NewQuestionForm(category=category,
                                       tutorial=tutorial, minute_range=minute_range,
                                       second_range=second_range)
                soup = BeautifulSoup(content, 'lxml')
                if soup.find_all('style'):
                    soup.style.decompose()
                content = soup.get_text()
                context['body'] = content.lstrip().rstrip()
                context['title2'] = title
                context['form'] = form
                return render(request,
                              'website/templates/new-question.html',
                              context)

            if resultspam == 1:
                warning = \
                    'Our system detects you have possibly entered a training \
                question. Do you want to post it over there?'
                category = request.POST.get('category', None)
                tutorial = 'General'
                minute_range = None
                second_range = None
                context['help'] = warning
                context['category'] = category

                # pass minute_range and second_range value to NewQuestionForm to populate on select

                form = NewQuestionForm(category=category,
                                       tutorial=tutorial, minute_range=minute_range,
                                       second_range=second_range)
                soup = BeautifulSoup(content, 'lxml')
                if soup.find_all('style'):
                    soup.style.decompose()
                content = soup.get_text()
                context['body'] = content.lstrip().rstrip()
                context['title'] = title
                context['form'] = form
                return render(request,
                              'website/templates/new-question.html',
                              context)

        form = NewQuestionForm(request.POST)
        if request.method == 'POST':
            question = Question()
            question.uid = request.user.id
            question.category = form['category'].value().replace(' ', '-')
            question.tutorial = form['tutorial'].value().replace(' ', '-')
            minute_range = 'None'
            second_range = 'None'
            question.minute_range = minute_range
            question.second_range = second_range
            question.title = form['title'].value()
            question.body = form['body'].value().encode('unicode_escape')
            if request.POST['action'] == 'Send for review':
                question.status = 0
                question.views = 1
                question.save()
                messages.success(request,
                                 'Your question has been sent for review. Check the site for further updates!'
                                 )
                return HttpResponseRedirect('/')
            question.views = 1
            question.save()
            return HttpResponseRedirect('/')
    else:

        # get values from URL.

        category = request.GET.get('category', None)
        tutorial = request.GET.get('tutorial', None)
        minute_range = request.GET.get('minute_range', None)
        second_range = request.GET.get('second_range', None)

        # pass minute_range and second_range value to NewQuestionForm to populate on select

        form = NewQuestionForm(category=category, tutorial=tutorial,
                               minute_range=minute_range,
                               second_range=second_range)
        context['category'] = category

    context['form'] = form
    context.update(csrf(request))
    return render(request, 'website/templates/new-question.html',
                  context)


@login_required
def new_question_general(request):
    context = {}
    if request.method == 'POST':
        if request.POST['action'] == 'Submit Question':
            content = request.POST['body']
            title = request.POST['title']
            category = request.POST['category']

            tutorial_detail_id = \
                TutorialDetails.objects.filter(foss__foss=category).values('foss'
                                                                           )

            resultspam = predictorspam(content,
                                       tutorial_detail_id[0]['foss'])
            warning = ''
            if resultspam == 0:
                warning = \
                    'Our system detects you have entered a text \
                that is not related to the tutorials directly or is not very clear .\
                Do you want admin to review the same?'
                context['help'] = warning
                category = request.POST.get('category', None)
                tutorial = request.POST.get('tutorial', None)
                minute_range = request.POST.get('minute_range', None)
                second_range = request.POST.get('second_range', None)

                # pass minute_range and second_range value to NewQuestionForm to populate on select

                form = NewQuestionForm(category=category,
                                       tutorial=tutorial, minute_range=minute_range,
                                       second_range=second_range)
                soup = BeautifulSoup(content, 'lxml')
                if soup.find_all('style'):
                    soup.style.decompose()
                content = soup.get_text()
                context['body'] = content.lstrip().rstrip()
                context['title2'] = title
                context['form'] = form
                return render(request,
                              'website/templates/new-question-general.html', context)

            if resultspam == 2:
                warning = \
                    'Our system detects you have entered a Tutorial \
                related content. Do you still want to post it ?'
                context['help'] = warning
                category = request.POST.get('category', None)
                tutorial = request.POST.get('tutorial', None)
                minute_range = request.POST.get('minute_range', None)
                second_range = request.POST.get('second_range', None)

                # pass minute_range and second_range value to NewQuestionForm to populate on select

                form = NewQuestionForm(category=category,
                                       tutorial=tutorial, minute_range=minute_range,
                                       second_range=second_range)
                soup = BeautifulSoup(content, 'lxml')
                if soup.find_all('style'):
                    soup.style.decompose()
                content = soup.get_text()
                context['body'] = content.lstrip().rstrip()
                context['title'] = title
                context['form'] = form
                return render(request,
                              'website/templates/new-question-general.html', context)

        form = NewQuestionForm(request.POST)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            question = Question()
            question.uid = request.user.id
            question.category = cleaned_data['category'].replace(' ',
                                                                 '-')
            question.tutorial = cleaned_data['tutorial'].replace(' ',
                                                                 '-')
            question.minute_range = cleaned_data['minute_range']
            question.second_range = cleaned_data['second_range']
            question.title = cleaned_data['title']
            question.body = cleaned_data['body'].encode('unicode_escape'
                                                        )
            if request.POST['action'] == 'Send for review':
                question.status = 0
                question.views = 1
                question.save()
                messages.success(request,
                                 'Your question has been sent for review. Check the site for further updates!'
                                 )
                return HttpResponseRedirect('/')
            question.views = 1
            question.save()
            return HttpResponseRedirect('/')
    else:

        # get values from URL.

        category = request.GET.get('category', None)
        tutorial = request.GET.get('tutorial', None)
        minute_range = request.GET.get('minute_range', None)
        second_range = request.GET.get('second_range', None)

        # pass minute_range and second_range value to NewQuestionForm to populate on select

        form = NewQuestionForm(category=category, tutorial=tutorial,
                               minute_range=minute_range,
                               second_range=second_range)
        context['category'] = category
    context['form'] = form
    context.update(csrf(request))
    return render(request, 'website/templates/new-question-general.html', context)

# Notification Section


@login_required
def user_questions(request, user_id):
    marker = 0
    if 'marker' in request.GET:
        marker = int(request.GET['marker'])

    if str(user_id) == str(request.user.id):
        total = Question.objects.filter(uid=user_id).count()
        total = int(total - (total % 10 - 10))
        questions = Question.objects.filter(uid=user_id).order_by('date_created').reverse()[marker:marker + 10]

        context = {
            'questions': questions,
            'total': total,
            'marker': marker
        }
        return render(request, 'website/templates/user-questions.html', context)
    return HttpResponse("go away")


@login_required
def user_answers(request, user_id):
    marker = 0
    if 'marker' in request.GET:
        marker = int(request.GET['marker'])

    if str(user_id) == str(request.user.id):
        total = Answer.objects.filter(uid=user_id).count()
        total = int(total - (total % 10 - 10))
        answers = Answer.objects.filter(uid=user_id).order_by('date_created').reverse()[marker:marker + 10]
        context = {
            'answers': answers,
            'total': total,
            'marker': marker
        }
        return render(request, 'website/templates/user-answers.html', context)
    return HttpResponse("go away")


@login_required
def user_notifications(request, user_id):
    if str(user_id) == str(request.user.id):
        notifications = Notification.objects.filter(uid=user_id).order_by('date_created').reverse()
        context = {
            'notifications': notifications
        }
        return render(request, 'website/templates/notifications.html', context)
    return HttpResponse("go away ...")


@login_required
def clear_notifications(request):
    Notification.objects.filter(uid=request.user.id).delete()
    return HttpResponseRedirect("/user/{0}/notifications/".format(request.user.id))


def search(request):
    context = {
        'categories': categories
    }
    return render(request, 'website/templates/search.html', context)

# Ajax Section
# All the ajax views go below


def ajax_category(request):
    context = {
        'categories': categories
    }
    return render(request, 'website/templates/ajax_categories.html', context)


def ajax_tutorials(request):
    if request.method == 'POST':
        category = request.POST.get('category')
        tutorials = TutorialDetails.objects.using('spoken').filter(
            foss__foss=category).order_by('level', 'order')
        context = {
            'tutorials': tutorials
        }
        return render(request, 'website/templates/ajax-tutorials.html', context)


def ajax_duration(request):
    if request.method == 'POST':
        category = request.POST['category']
        tutorial = request.POST['tutorial']
        video_detail = TutorialDetails.objects.using('spoken').get(
            Q(foss__foss=category),
            Q(tutorial=tutorial)
        )
        video_resource = TutorialResources.objects.using('spoken').get(
            Q(tutorial_detail_id=video_detail.id),
            Q(language__name='English')
        )
        video_path = '{0}/{1}/{2}/{3}'.format(
            VIDEO_PATH,
            str(video_detail.foss_id),
            str(video_detail.id),
            video_resource.video
        )

        video_info = get_video_info(video_path)

        # convert minutes to 1 if less than 0
        # convert seconds to nearest upper 10th number eg(23->30)
        minutes = video_info['minutes']
        seconds = video_info['seconds']
        if minutes < 0:
            minutes = 1
        seconds = int(seconds - (seconds % 10 - 10))
        seconds = 60
        context = {
            'minutes': minutes,
            'seconds': seconds,
        }
        return render(request, 'website/templates/ajax-duration.html', context)


@login_required
def ajax_question_update(request):
    if request.method == 'POST':
        qid = request.POST['question_id']
        title = request.POST['question_title']
        body = request.POST['question_body']
        question = get_object_or_404(Question, pk=qid)
        if can_edit(user=request.user, obj=question):
            question.title = title
            question.body = body.encode('unicode_escape')
            question.save()
            return HttpResponse("saved")

    return HttpResponseForbidden("Not Authorised")


@login_required
def ajax_details_update(request):
    if request.method == 'POST':
        qid = request.POST['qid']
        category = request.POST['category']
        tutorial = request.POST['tutorial']
        minute_range = request.POST['minute_range']
        second_range = request.POST['second_range']
        question = get_object_or_404(Question, pk=qid)
        if can_edit(user=request.user, obj=question):
            question.category = category
            question.tutorial = tutorial
            question.minute_range = minute_range
            question.second_range = second_range
            question.save()
            return HttpResponse("saved")

    return HttpResponseForbidden("Not Authorised")


@login_required
def ajax_answer_update(request):
    if request.method == 'POST':
        aid = request.POST['answer_id']
        body = request.POST['answer_body']
        answer = get_object_or_404(Answer, pk=aid)
        if can_edit(user=request.user, obj=answer):
            answer.body = body.encode('unicode_escape')
            answer.save()
            return HttpResponse("saved")

    return HttpResponseForbidden("Not Authorised")


@login_required
def ajax_answer_comment_update(request):
    if request.method == "POST":
        comment_id = request.POST["comment_id"]
        comment_body = request.POST["comment_body"]
        comment = get_object_or_404(AnswerComment, pk=comment_id)
        if can_edit(user=request.user, obj=comment):
            comment.body = comment_body.encode('unicode_escape')
            comment.save()
            return HttpResponse("saved")

    return HttpResponseForbidden("Not Authorised")


def ajax_similar_questions(request):
    if request.method == 'POST':
        category = request.POST['category']
        tutorial = request.POST['tutorial']
        # minute_range = request.POST['minute_range']
        # second_range = request.POST['second_range']

        # add more filtering when the forum grows
        questions = Question.objects.filter(category=category).filter(tutorial=tutorial)
        context = {
            'questions': questions
        }
        return render(request, 'website/templates/ajax-similar-questions.html', context)


@login_required
def ajax_notification_remove(request):
    if request.method == "POST":
        nid = request.POST["notification_id"]
        notification = get_object_or_404(Notification, pk=nid)
        if notification.uid == request.user.id:
            notification.delete()
            return HttpResponse("removed")
    return HttpResponseForbidden("failed")


@login_required
def ajax_delete_question(request):
    result = False
    if request.method == "POST":
        key = request.POST['question_id']
        question = get_object_or_404(Question, pk=key)
        if can_edit(user=request.user, obj=question):
            question.delete()
            result = True
    return HttpResponse(json.dumps(result), mimetype='application/json')


@login_required
def ajax_hide_question(request):
    result = False
    if request.method == "POST":
        key = request.POST['question_id']
        question = get_object_or_404(Question, pk=key)
        if can_edit(user=request.user, obj=question):
            question.status = 0
            if request.POST['status'] == '0':
                question.status = 1
            question.save()
            result = True
    return HttpResponse(json.dumps(result), mimetype='application/json')


def ajax_keyword_search(request):
    if request.method == "POST":
        key = request.POST['key']
        questions = Question.objects.filter(title__icontains=key, status=1)
        context = {
            'questions': questions
        }
        return render(request, 'website/templates/ajax-keyword-search.html', context)


def ajax_time_search(request):
    if request.method == "POST":
        category = request.POST.get('category')
        tutorial = request.POST.get('tutorial')
        minute_range = request.POST.get('minute_range')
        second_range = request.POST.get('second_range')
        questions = None
        if category:
            questions = Question.objects.filter(category=category.replace(' ', '-'), status=1)
        if tutorial:
            questions = questions.filter(tutorial=tutorial.replace(' ', '-'))
        if minute_range:
            questions = questions.filter(category=category.replace(
                ' ', '-'), tutorial=tutorial.replace(' ', '-'), minute_range=minute_range)
        if second_range:
            questions = questions.filter(category=category.replace(
                ' ', '-'), tutorial=tutorial.replace(' ', '-'), second_range=second_range)
        context = {
            'questions': questions
        }
        return render(request, 'website/templates/ajax-time-search.html', context)


def ajax_vote(request):
    # for future use
    pass


def forums_mail(to='', subject='', message=''):
    # Start of email send
    email = EmailMultiAlternatives(
        subject, '', 'forums',
        to.split(','),
        headers={"Content-type": "text/html;charset=iso-8859-1"}
    )
    email.attach_alternative(message, "text/html")
    email.send(fail_silently=True)
    # End of email send

# daily notifications for unanswered questions.


def unanswered_notification(request):
    questions = Question.objects.all()
    total_count = 0
    message = """
        The following questions are left unanswered.
        Please take a look at them. <br><br>
    """
    for question in questions:
        if not question.answer_set.count():
            total_count += 1
            message += """
                #{0}<br>
                Title: <b>{1}</b><br>
                Category: <b>{2}</b><br>
                Link: <b>{3}</b><br>
                <hr>
            """.format(
                total_count,
                question.title,
                question.category,
                'http://forums.spoken-tutorial.org/question/' + str(question.id)
            )
    to = "team@spoken-tutorial.org, team@fossee.in"
    subject = "Unanswered questions in the forums."
    if total_count:
        forums_mail(to, subject, message)
    return HttpResponse(message)
