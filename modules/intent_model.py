import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

training_sentences = [
    "login",
    "log in",
    "sign in",
    "read email",
    "read my mail",
    "send email",
    "compose email",
    "count email",
    "how many emails",
    "exit",
    "stop assistant"
]

labels = [
    "login",
    "login",
    "login",
    "read_email",
    "read_email",
    "send_email",
    "send_email",
    "count_email",
    "count_email",
    "exit",
    "exit"
]

vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(training_sentences)

model = LogisticRegression()
model.fit(X, labels)

def predict_intent(text):
    X_test = vectorizer.transform([text])
    return model.predict(X_test)[0]