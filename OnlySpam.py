import pandas as pd
from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import TfidfVectorizer
from imblearn.over_sampling import SMOTE
import re
from sklearn.svm import LinearSVC
import pickle 
fields = ['Content','Spam']

df = pd.read_csv('OnlySpam.csv',usecols=fields,skipinitialspace=True)
#TAG_RE = re.compile(r'<a.*?>.*?</a>')

def remove_tags(text):
#    string = TAG_RE.sub('hyperlink',text)
    soup = BeautifulSoup(text,"lxml")
    if soup.find_all('style'):
        soup.style.decompose()
    string = soup.get_text()
    string = string.replace('&nbsp;','').replace('\n','').replace('\r','').replace('\t','')
    string = ' '.join([w for w in string.split() if len(w)>=3])
    return string

df['Content']=df['Content'].apply(remove_tags)

vectorizer = TfidfVectorizer(stop_words='english')

x_train = vectorizer.fit_transform(df['Content'])

#sm = SMOTE(random_state=42)

#x_train,y_train = sm.fit_sample(x_train,df['Spam'])


model = LinearSVC()

model.fit(x_train,df['Spam'])
filename = 'spam_model.sav'

pickle.dump(model, open(filename, 'wb'))

def predictorspam(comment):
    simplified = remove_tags(comment)
    tester = [simplified]
    contest = vectorizer.transform(tester)
    load_model = pickle.load(open(filename, 'rb'))
    a = load_model.predict(contest)
    return a[0]

