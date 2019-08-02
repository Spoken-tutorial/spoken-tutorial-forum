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

def predictorspam(comment, foss_id, tdid):
    clean_data = os_walk(foss_id, tdid)
    clean_data = clean_data.split(".")
    my_dict = {}

    for data in clean_data:
        try:
            my_dict["Content"].append(data)
            my_dict["Spam"].append(2)
        except:
            my_dict["Content"] = [data]
            my_dict["Spam"] = [2]
            
    # 0 - Spam
    # 1 - Training related
    # 2 - Tutorial related
    new_df = pd.DataFrame(data=my_dict)
    df = pd.read_csv('cuss.csv', usecols=fields, skipinitialspace=True)
    frame = [new_df,df]
    result_df = pd.concat(frame)

    result_df['Content'] = result_df['Content'].apply(remove_tags)
    vectorizer = TfidfVectorizer(stop_words='english')
    x_train = vectorizer.fit_transform(result_df['Content'])
    model = LinearSVC()

    model.fit(x_train, result_df['Spam'])
    filename = 'spam_model.sav'

    pickle.dump(model, open(filename, 'wb'))
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
def get_script_data(root,file):
    data = ""
    with open(root+'/'+file) as docfile:
        print "\n==================="
        data += docfile.read()
        print "\n==================="

        data_parsed = re.sub('[^A-Z a-z .]+', '', data)
        return data_parsed.lower()

#VIDEO_PATH = '/datas/websites/saurabh-a/spoken-website/media/videos/'
from config import VIDEO_PATH
def os_walk(foss_id, tdid):
    data = ""
    filepath = VIDEO_PATH +'/' +str(foss_id) + '/'
    print "filepath :",filepath
    
    for root, dirs, files in os.walk(filepath):
        if not dirs:
            print(root, "is a directory without subdirectories")
            # do whatever you need to do with your files here
        else:
            print "root : ",root
            print "dirs : ", dirs
            #files = [ fi for fi in files if fi.endswith("English.srt") ]
            for folder in dirs:
                print("{0} - {1}".format(type(folder),type(tdid)))
                if folder == str(tdid):
                    sub_filepath = filepath + folder + '/'
                    for sub_root, sub_dirs, sub_files in os.walk(sub_filepath):
                        if sub_dirs:
                            files = [ fi for fi in sub_files if fi.endswith("English.srt") ]
                            print "--",files
                            for file in files:
                                data += get_script_data(sub_root,file)

        return data
            