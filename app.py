from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
import numpy as np
import pandas as pd
import pickle
import requests
from collections import OrderedDict
# app.py (Top of the file)
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash # <-- ADD THIS
# ... (rest of imports)

# -----------------------------------------
# Initialize Flask App
# -----------------------------------------
app = Flask(__name__)
app.secret_key = "abc123"

# -----------------------------------------
# Database Configuration (SQLite)
# -----------------------------------------
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# -----------------------------------------
# Database Model
# -----------------------------------------
# app.py (Database Model)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    # Increased size to 255 to store the long password hash
    password = db.Column(db.String(255), nullable=False) 

    def set_password(self, password):
        """Hashes the password and stores it."""
        self.password = generate_password_hash(password)

    def check_password(self, password):
        """Checks the provided password against the hash."""
        return check_password_hash(self.password, password)

# -----------------------------------------
# Load ML Model, Preprocessor & Data
# -----------------------------------------
dtr = pickle.load(open('dtr.pkl', 'rb'))
preprocessor = pickle.load(open('preprocessor.pkl', 'rb'))
df = pd.read_csv('yield_df.csv.zip')

areas = sorted(df['Area'].unique())
crops = sorted(df['Item'].unique())

# -----------------------------------------
# Weather Function
# -----------------------------------------
def get_weather(area):
    try:
        url = f"https://geocoding-api.open-meteo.com/v1/search?name={area}&count=1"
        res = requests.get(url, timeout=5).json()
        if "results" not in res:
            return None
        lat, lon = res["results"][0]["latitude"], res["results"][0]["longitude"]

        wurl = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&timezone=auto"
        wres = requests.get(wurl, timeout=5).json()
        temp_max = np.mean(wres["daily"]["temperature_2m_max"])
        temp_min = np.mean(wres["daily"]["temperature_2m_min"])
        avg_temp = round((temp_max + temp_min) / 2, 2)
        avg_rain = round(np.sum(wres["daily"]["precipitation_sum"]) / 12, 2)
        return {"avg_temp": avg_temp, "average_rain_fall_mm_per_year": avg_rain}
    except Exception:
        return None

# -----------------------------------------
# Routes: Login / Signup / Logout
# -----------------------------------------
@app.route('/')
def home():
    if "user" in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

# app.py (Routes: /login)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        uname = request.form['username']
        pwd = request.form['password']
        
        # --- SECURED CHANGE HERE ---
        # 1. Retrieve user by username only
        user = User.query.filter_by(username=uname).first()
        
        # 2. Check if user exists AND if the password matches the hash
        if user and user.check_password(pwd):
        # --------------------------
            session['user'] = uname
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Invalid username or password")
    return render_template('login.html')


# app.py (Routes: /signup)
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        uname = request.form['username']
        pwd = request.form['password']
        existing_user = User.query.filter_by(username=uname).first()
        if existing_user:
            return render_template('signup.html', error="User already exists")
        
        # --- SECURED CHANGE HERE ---
        new_user = User(username=uname)
        new_user.set_password(pwd) # Hash and set the password
        # --------------------------
        
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

# -----------------------------------------
# Dashboard & Prediction
# -----------------------------------------
@app.route('/dashboard')
def dashboard():
    if "user" not in session:
        return redirect(url_for('login'))
    return render_template('index.html', areas=areas, crops=crops)

@app.route('/get_weather/<area>')
def fetch_weather(area):
    data = get_weather(area)
    if data:
        return jsonify(data)
    else:
        return jsonify({"avg_temp": 25, "average_rain_fall_mm_per_year": 1200})

@app.route('/predict', methods=['POST'])
def predict():
    if "user" not in session:
        return redirect(url_for('login'))
    try:
        year = int(request.form['Year'])
        rainfall = float(request.form['average_rain_fall_mm_per_year'])
        pesticides = float(request.form['pesticides_tonnes'])
        avg_temp = float(request.form['avg_temp'])
        area = request.form['Area']
        selected_crops = request.form.getlist('Item')

        multi_predictions = OrderedDict()

        for crop in selected_crops:
            sample = pd.DataFrame([{
                'Year': year,
                'average_rain_fall_mm_per_year': rainfall,
                'pesticides_tonnes': pesticides,
                'avg_temp': avg_temp,
                'Area': area,
                'Item': crop
            }])
            processed = preprocessor.transform(sample)
            pred = dtr.predict(processed)[0]
            multi_predictions[crop] = round(pred, 2)

        crop = selected_crops[0]
        crop_data = df[(df['Area'] == area) & (df['Item'] == crop)].groupby('Year')['hg/ha_yield'].mean()
        yield_trend = crop_data.tail(10).to_dict()
        yield_trend[year] = list(multi_predictions.values())[0]

        return render_template(
            'index.html',
            areas=areas,
            crops=crops,
            selected_area=area,
            selected_crops=selected_crops,
            multi_predictions=multi_predictions,
            yield_trend=yield_trend
        )
    except Exception as e:
        return render_template(
            'index.html',
            areas=areas,
            crops=crops,
            error_message=f"❌ Error: {str(e)}"
        )

# -----------------------------------------
# Run App
# -----------------------------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Creates users.db file automatically
    app.run(debug=True)
