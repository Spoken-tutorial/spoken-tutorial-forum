# Libraries
import pandas as pd
from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
# from nltk import word_tokenize
# from nltk.stem import WordNetLemmatizer
import pickle
from imblearn.over_sampling import SMOTE
fields = ['Content', 'Label']

# Load into dataframe
df = pd.read_csv('STdataset.csv', skipinitialspace=True, usecols=fields)

# Stripping function


def remove_tags(text):
    soup = BeautifulSoup(text, "lxml")
    if soup.find_all('style'):
        soup.style.decompose()
    string = soup.get_text()
    string = string.replace('&nbsp;', '').replace(
        '\n', '').replace('\r', '').replace('\t', '')
    string = ' '.join([w for w in string.split() if len(w) >= 3])
    return string


df['Content'] = df['Content'].apply(remove_tags)

# Lemmatizer

'''
class LemmaTokenizer(object):
    def __init__(self):
        self.wnl = WordNetLemmatizer()

    def __call__(self, doc):
        return [self.wnl.lemmatize(t) for t in word_tokenize(doc)]
'''

# Vectorizer
vectorizer = TfidfVectorizer(stop_words='english')

x = vectorizer.fit_transform(df['Content'])

# Minority oversampling
sm = SMOTE(random_state=42)

x, y = sm.fit_sample(x, df['Label'])

# Model fitting
model = LinearSVC(random_state=42, tol=5, fit_intercept=False)
model.fit(x, y)
filename = 'tutorial_model.sav'
pickle.dump(model, open(filename, 'wb'))

# Predictor function


def predictor(comment):
    simplified = remove_tags(comment)
    tester = [simplified]
    print(simplified)
    contest = vectorizer.transform(tester)
    load_model = pickle.load(open(filename, 'rb'))
    a = load_model.predict(contest)
    return a[0]
