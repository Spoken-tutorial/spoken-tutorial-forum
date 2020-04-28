#from fuzzywuzzy import fuzz, process
from website.models import Question, Answer, Notification, AnswerComment
from spoken_auth.models import FossCategory, TutorialDetails
from os.path import dirname, curdir, realpath
import re, csv
def existing_question(content, category, tutorial):
    foss_id = FossCategory.objects.filter(foss = category)    
    tutorial_detail = TutorialDetails.objects.filter(tutorial = tutorial)
    keywords = TutorialCommonContents.objects.get(tutorial_detail = tutorial_detail)
    foss_name = slugify_me(str(category))
    tutorial = slugify_me(str(tutorial))
    user_ques_parsed = remove_tags(parse_html(str(content)))
    #user_ques_formatted = vectorizer.fit_transform(user_ques_parsed)
    questions = Question.objects.filter(category=foss_name, tutorial=tutorial)
    parsed_question = []
    log =[]
    for question in questions:
        
        this_question = remove_tags(parse_html(str(question.body)))
        if len(this_question)>4:
            parsed_question.append(this_question)
            log.append((this_question,question.id,fuzz.token_sort_ratio(user_ques_parsed, this_question)))
            #formatted_question = vectorizer.fit_transform(parsed_question)
            #print "->",process.extract(user_ques_parsed, this_question)
    highest = process.extract(user_ques_parsed, parsed_question)
    

def slugify_me(text):
    data = text.strip().replace(' ','-')
    return data

def parse_html(text):
    soup = BeautifulSoup(text, 'html.parser')
    return soup.get_text()

def takeThird(elem):
    return elem[2]

import re
def striphtml(data):
    p = re.compile(r'<.*?>')
    return p.sub('', data)


def check_for_cuss(text):
    #text = striphtml(text)
    dir_path = dirname(realpath(__file__))
    filepath = dir_path+'/'+'cuss.csv'
    body = re.split(', | ',str(text).lower().strip())
    with open(filepath,'r') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',')
        for spam in spamreader:
            for word in body:
                if word in spam:
                    return True
            return False

def remove_stop_words(text):
    #text = striphtml(text)
    title_words = re.split(', | ',str(text).lower())
    print("My words are :",title_words)
    important_words = []
    dir_path = dirname(realpath(__file__))
    filepath = dir_path+'/'+'stopwords_English.csv'
    with open(filepath,'r') as csvfile:
        stop_words = csv.reader(csvfile, delimiter=',')
        for a_word in title_words:
            if a_word not in stop_words :
                important_words.append(a_word)
    print("important_words : ",important_words)
    return important_words
