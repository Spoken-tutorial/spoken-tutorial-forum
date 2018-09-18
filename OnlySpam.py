import pandas as pd
from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
import pickle
fields = ['Content', 'Spam']

df = pd.read_csv('OnlySpam.csv', usecols=fields, skipinitialspace=True)
# TAG_RE = re.compile(r'<a.*?>.*?</a>')


def remove_tags(text):
    # string = TAG_RE.sub('hyperlink',text)
    soup = BeautifulSoup(text, "lxml")
    if soup.find_all('style'):
        soup.style.decompose()
    string = soup.get_text()
    string = string.replace('&nbsp;', '').replace(
        '\n', '').replace('\r', '').replace('\t', '')
    string = ' '.join([w for w in string.split() if len(w) >= 3])
    return string


df['Content'] = df['Content'].apply(remove_tags)

vectorizer = TfidfVectorizer(stop_words='english')

x_train = vectorizer.fit_transform(df['Content'])

model = LinearSVC()

model.fit(x_train, df['Spam'])
filename = 'spam_model.sav'

pickle.dump(model, open(filename, 'wb'))
from django.conf import settings

def predictorspam(comment,tdid):
    clean_data = os_walk(tdid)
    simplified = remove_tags(comment)
    tester = [simplified]
    contest = vectorizer.transform(tester)
    load_model = pickle.load(open(filename, 'rb'))
    a = load_model.predict(contest)
    #Error here
    #a = load_model.predict(clean_data)
    return a[0]
import re
import os
def get_data(root,file):
    data = ""
    with open(root+'/'+file) as docfile:
        print "\n==================="
        data += docfile.read()
        print "\n==================="
        data_parsed = re.sub('[^A-Z a-z]+', '', data)
        return data_parsed.lower()

VIDEO_PATH = '/datas/websites/saurabh-a/spoken-website/media/videos/'
def os_walk(tdid):
    data = ""
    filepath = VIDEO_PATH + str(tdid) + '/'
    print "filepath :",filepath
    
    for root, dirs, files in os.walk(filepath):
        if not dirs:
            print(root, "is a directory without subdirectories")
            # do whatever you need to do with your files here
        else:
            print "root : ",root
            print "dirs : ", dirs
            files = [ fi for fi in files if fi.endswith("English.srt") ]
            print "files found are : \n",files
            for file in files:
                data += get_data(root,file)

        return data
            