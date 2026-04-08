import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
import os

# Sample dataset
data = [
    ("Huge potholes on the main street", "Road Damage"),
    ("Water pipe leakage causing flooding", "Water Supply"),
    ("Power outage since morning", "Electricity"),
    ("Garbage not collected in area", "Garbage"),
    ("There was a mugging last night", "Public Safety"),
    ("Street light broken", "Electricity"),
    ("Overflowing trash bin", "Garbage"),
    ("Bridge crack increasing", "Road Damage"),
    ("Leak in water supply causing contamination", "Water Supply"),
    ("Minor road paint needed", "Road Damage"),
]

texts = [t[0] for t in data]
labels = [t[1] for t in data]

vectorizer = TfidfVectorizer(max_features=1000, ngram_range=(1,2))
X = vectorizer.fit_transform(texts)

clf = LogisticRegression(max_iter=500)
clf.fit(X, labels)

# Save model + vectorizer
out_dir = os.path.join(os.getcwd())
model_path = os.path.join(out_dir, 'model.joblib')
vec_path = os.path.join(out_dir, 'vectorizer.joblib')
joblib.dump({'model': clf}, model_path)
joblib.dump(vectorizer, vec_path)

print('Saved model.joblib and vectorizer.joblib in', out_dir)
