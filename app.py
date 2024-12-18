from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# Configure SQLite database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///details.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# Define a database model
class UserDetail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    symptoms = db.Column(db.Text, nullable=False)
    medical_history = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


with app.app_context():
    db.create_all()

# Route for index page
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/form", methods=["GET", "POST"])
def form_page():
    if request.method == "POST":
        name = request.form.get("name")
        age = request.form.get("age")
        medical_history = request.form.get("history")
        
        # Collect all checked symptom checkboxes
        symptom_checkboxes = [
            "fever", "fatigue", "shivering", "weight_loss", "appetite_loss",   # General Symptoms
            "cough", "short_breath", "chest_pain", "nasal_congestion", "sore_throat",  # Respiratory Symptoms
            "nausea", "vomiting", "diarrhea", "constipation", "heartburn",    # Gastrointestinal Symptoms
            "headache", "dizziness", "numbness", "blurred_vision"  # Neurological Symptoms
        ]
        
        # Filter only checked boxes
        selected_symptoms = [symptom for symptom in symptom_checkboxes if request.form.get(symptom)]
        checkbox_symptoms = ", ".join(selected_symptoms)  # Convert list to string

        # Collect "other symptoms" from the textbox
        other_symptoms = request.form.get("other_symptoms", "").strip()
        
        # Combine all symptoms into a single string
        all_symptoms = ", ".join(filter(None, [checkbox_symptoms, other_symptoms]))

        # Print to console (you can replace this logic to use the `all_symptoms` string)
        print("All Symptoms:", all_symptoms)

        try:
            # Save only necessary fields to the database
            new_entry = UserDetail(
                name=name, 
                age=age, 
                medical_history=medical_history
            )
            db.session.add(new_entry)
            db.session.commit()
            return redirect(url_for("result_page"))
        except:
            return "There was an issue saving the data."

    return render_template("diagnose/form.html")


# Route for result page
@app.route("/result")
def result():
    users = UserDetail.query.all()
    return render_template("result.html", users=users)

# About page route
@app.route("/about")
def about_page():
    return "<h1 style='text-align: center;'>About Us</h1>"

# Contact page route
@app.route("/contact")
def contact_page():
    return "<h1 style='text-align: center;'>Contact Us</h1>"

if __name__ == "__main__":
    app.run(debug=True)
