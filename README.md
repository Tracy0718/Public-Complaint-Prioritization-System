AI Public Complaint Prioritization System

Quick start (Windows):

1. Create venv and activate
   python -m venv venv
   venv\Scriptsctivate

2. Install dependencies
   pip install -r requirements.txt

3. Migrate DB
   python manage.py migrate

4. Create superuser
   python manage.py createsuperuser

5. Train ML model
   cd complaints/ml
   python train_model.py
   # generated model.joblib & vectorizer.joblib will be placed in complaints/ml/

6. Run server
   python manage.py runserver

7. Visit http://127.0.0.1:8000/
