import re
from website.models import Question
from nltk.corpus import stopwords 
from nltk.tokenize import word_tokenize
from sklearn.metrics.pairwise import cosine_similarity
sw = stopwords.words('english')

def get_video_info(path):
    """Uses ffmpeg to determine information about a video. This has not been broadly
    tested and your milage may vary"""

    from decimal import Decimal
    import subprocess
    import re

    process = subprocess.Popen(['/usr/bin/ffmpeg', '-i', path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdout, stderr = process.communicate()
    duration_m = re.search(r"Duration:\s{1}(?P<hours>\d+?):(?P<minutes>\d+?):(?P<seconds>\d+\.\d+?)", stdout.decode("UTF-8"), re.DOTALL).groupdict()
    info_m = re.search(r": Video: (?P<codec>.*?), (?P<profile>.*?), (?P<width>.*?)x(?P<height>.*?), ", stdout.decode("UTF-8"), re.DOTALL).groupdict()
    hours = Decimal(duration_m['hours'])
    minutes = Decimal(duration_m['minutes'])
    seconds = Decimal(duration_m['seconds'])

    total = 0
    total += 60 * 60 * hours
    total += 60 * minutes
    total += seconds

    info_m['hours'] = hours
    info_m['minutes'] = minutes
    info_m['seconds'] = seconds
    info_m['duration'] = total
    return info_m


def prettify(string):
    string = string.lower()
    string = string.replace('-', ' ')
    string = string.strip()
    string = string.replace(' ', '-')
    string = re.sub('[^A-Za-z0-9\-]+', '', string)
    string = re.sub('-+', '-', string)
    return string


def pre_process(text):
    text=text.lower()                       # lowercase
    text = re.sub('<.*?>', ' ', text).replace('  ',' ')
    text=re.sub("<!--?.*?-->"," ",text).replace('  ',' ')      # remove tags
    text=re.sub("(\\d|\\W)+"," ",text).replace('  ',' ')      # remove special characters and digits
    return text

def clean_user_data(text):
    words = word_tokenize(pre_process(text.lower()))
    clean_list = [w for w in words if not w in sw]
    return clean_list

def get_similar_questions(user_ques,question):
    total = []
    l1 = []
    l2 = []
    question = word_tokenize(pre_process(question))
    question =[w for w in question if not w in sw]
    total = user_ques + question
    for w in total: 
        if w in user_ques: l1.append(1) # create a vector 
        else: l1.append(0) 
        if w in question: l2.append(1) 
        else: l2.append(0)        
    cs = cosine_similarity((l1,l2))
    return cs[0][1]