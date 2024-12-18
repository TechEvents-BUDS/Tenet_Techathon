from io import BytesIO
import os
from PIL import Image
import PIL
from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime
api_keyy = "AIzaSyDnD3hfDeffjAV1n9gW-3cEDh86WbUFrzw"
import google.generativeai as genai
from werkzeug.utils import secure_filename


app = Flask(__name__)
app.secret_key = api_keyy  # Needed for using session
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Route for index page
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/form", methods=["GET", "POST"])
def form_page():
    if request.method == "POST":
        # Collect form data
        name = request.form.get("name")
        gender = request.form.get("gender")  # Gender field
        age = request.form.get("age")
        onset = request.form.get("onset")  # When symptoms began
        severity = request.form.get("severity")
        aggravating_factors = request.form.get("aggravating_factors")
        relieving_factors = request.form.get("relieving_factors")
        past_medical_history = request.form.get("past_medical_history")
        medications = request.form.get("medications")
        family_history = request.form.get("family_history")
        
        # List of symptoms to be checked
        symptom_names = [
            "fever", "fatigue_tiredness", "chills_or_shivering", "sweating_night_sweats", "weight_loss_unexplained",
            "weight_gain", "loss_of_appetite", "cough_dry_or_productive", "shortness_of_breath", "chest_pain",
            "wheezing", "nasal_congestion", "sore_throat", "sneezing", "palpitations", "chest_tightness", "dizziness",
            "swelling_in_legs", "fainting", "abdominal_pain", "nausea", "vomiting", "diarrhea", "constipation", "bloating",
            "heartburn", "headache", "weakness_in_limbs", "numbness_tingling", "seizures", "confusion", "blurred_vision",
            "rash", "itching", "redness", "bruising", "dry_flaky_skin", "yellowing_of_skin", "anxiety", "depression",
            "mood_swings", "insomnia", "poor_concentration", "irritability"
        ]
        
        # Filter the checked checkboxes
        selected_symptoms = [symptom for symptom in symptom_names if request.form.get(symptom)]
        checkbox_symptoms = ", ".join(selected_symptoms)  # Join selected symptoms into a string

        # Collect "other symptoms" from the textbox
        other_symptoms = request.form.get("other_symptoms", "").strip()

        # Combine all symptoms (checkbox and other symptoms) into one string
        all_symptoms = ", ".join(filter(None, [checkbox_symptoms, other_symptoms]))

        # Store all form data in session for later use on the result page
        session["name"] = name
        session["gender"] = gender
        session["age"] = age
        session["onset"] = onset
        session["severity"] = severity
        session["aggravating_factors"] = aggravating_factors
        session["relieving_factors"] = relieving_factors
        session["past_medical_history"] = past_medical_history
        session["medications"] = medications
        session["family_history"] = family_history
        session["symptoms"] = all_symptoms

        return redirect(url_for("result"))

    return render_template("diagnose/form.html")


@app.route("/result")
def result():
    # Retrieve the stored data from the session
    name = session.get("name")
    age = session.get("age")
    gender = session.get("gender")
    onset = session.get("onset")
    severity = session.get("severity")
    aggravating_factors = session.get("aggravating_factors")
    relieving_factors = session.get("relieving_factors")
    past_medical_history = session.get("past_medical_history")
    medications = session.get("medications")
    family_history = session.get("family_history")
    symptoms = session.get("symptoms")

    # Render the result page with all variables
    
    prompt = f"Patient Information: Age: {age}\nGender: {gender}\nSymptoms: {symptoms}\n"
    prompt += f"Severity: {severity}\nSymtoms begain {onset} ago\nAggravating Factors: {aggravating_factors}\n"
    prompt += f"Relieving Factors: {relieving_factors}\nPast Medical History: {past_medical_history}\n"
    prompt += f"Medications currently on: {medications}\nFamily History: {family_history}\n"
    prompt += " We are a diagnosing answer on our behalf. Give the answer in html format so I can display on website.Give it without any structure tags such as html or body etc, also no main heading I have that put already, also do not try to format it for line gaps and etc just give a br at max or make lists if you want. First provide with a sysmtom analysis and an alert if it is, then Recommeneded steps (Which doctor to consult, or tests, lifestyle tips), Medicines that can be taken prescription for temporary purpose (For simple deceases recommend it like they can take it and for extreme cases give pain relif medications). Give your answers in the following format by paragraph. Symptoms ,medicine recommended , Tests (if required), Further recommendations. If you want any more information ask right now"
    prompt += "Many people find it hard to manage their health due to: • Ignoring small symptoms until they turn into serious health issues. • Not knowing which doctor to consult or what to do next. • Struggling to maintain healthy habits like proper exercise, diet, or stress management. People with chronic diseases (like diabetes, high blood pressure, or mental health issues) especially need constant guidance and tracking. This is our problem satement so make sure these points are convered underneath"
    
    genai.configure(api_key=api_keyy)
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    
    reply = response.text
    print(reply)
    
    return render_template("result.html", 
                           name=name, 
                           age=age, 
                           gender=gender,
                           onset=onset,
                           severity=severity,
                           aggravating_factors=aggravating_factors,
                           relieving_factors=relieving_factors,
                           past_medical_history=past_medical_history,
                           medications=medications,
                           family_history=family_history,
                           symptoms=symptoms,
                           response=reply)

def ai_diagnose_image(file_stream):
    sample_file_1 = PIL.Image.open(file_stream)  # Open directly from file stream
    genai.configure(api_key=api_keyy)
    model = genai.GenerativeModel(model_name="gemini-1.5-pro")
    prompt = "List possibilities for this infection. I want no additional text besides a list with each element separated by a comma"
    response = model.generate_content([prompt, sample_file_1])
    possibilities = (response.text).split(',')

    prompt1 = f"For each disease in {possibilities}, provide me a list of tests that a doctor may ask a patient to take to confirm the issue. Present the answer in the following format: Disease: list of tests separated by commas."
    response1 = model.generate_content([prompt1, sample_file_1])
    tests = response1.text

    print('Based on your image, here are some possibilities:')
    for possibility in possibilities:
        print(f'- {possibility}')

    print('\nBased on these possibilities, here are some tests a medical professional might ask you to take:')
    print(tests)

    return tests  # Return the tests info for use in the template

@app.route("/result_image", methods=["GET", "POST"])
def result_image():
    diagnosis = None
    uploaded_file = None
    possibilities = None
    tests = None
    
    if request.method == "POST":
        # Check if a file was uploaded
        if 'image' not in request.files:
            return render_template("result_image.html", error="No file part")

        file = request.files['image']
        if file.filename == '':
            return render_template("result_image.html", error="No selected file")
        
        if file and allowed_file(file.filename):
            # Secure the filename and save the file
            filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filename)
            uploaded_file = file.filename  # Optionally, pass the filename to the template

            # Pass the file stream to ai_diagnose_image for diagnosis
            possibilities, tests = ai_diagnose_image(file.stream)  # Pass file.stream instead of file path

    return render_template("result_image.html", diagnosis=possibilities, tests=tests, uploaded_file=uploaded_file)



@app.route("/vs", methods=["GET", "POST"])
def vs():
    diagnosis = None
    uploaded_file = None
    
    if request.method == "POST":
        # Check if a file was uploaded
        if 'image' not in request.files:
            return render_template("diagnose/vs.html", error="No file part")

        file = request.files['image']
        if file.filename == '':
            return render_template("diagnose/vs.html", error="No selected file")
        
        if file and allowed_file(file.filename):
            # Secure the filename and process the image in memory
            print(file.filename)

            # Pass the file stream to ai_diagnose_image
            diagnosis = ai_diagnose_image(file.stream)  # Pass file.stream instead of file path
            uploaded_file = file.filename  # Optionally, pass the filename to the template

            # After AI diagnosis, render the result_image.html page with the results
            return render_template("diagnose/result_image.html", diagnosis=diagnosis, uploaded_file=uploaded_file)

    return render_template("diagnose/vs.html", diagnosis=diagnosis, uploaded_file=uploaded_file)




def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


if __name__ == "__main__":
    app.run(debug=True)
