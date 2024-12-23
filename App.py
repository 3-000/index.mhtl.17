from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
import speech_recognition as sr
import pyttsx3
from werkzeug.security import generate_password_hash, check_password_hash
import random
import base64

# Flask App and Configuration
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///saliver.db'
app.config['SECRET_KEY'] = 'your_secret_key_here'

# Initialize Database and SocketIO
db = SQLAlchemy(app)
socketio = SocketIO(app)

# Initialize Speech Recognition and Text-to-Speech
recognizer = sr.Recognizer()
engine = pyttsx3.init()

# User Data Storage
users = {"0308025349802":"Sphiwe"}

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    voiceprint = db.Column(db.String, nullable=True)  # Encoded voiceprint

class Command(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    command_text = db.Column(db.String, nullable=False)
    response_text = db.Column(db.String, nullable=False)

# Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    """Register a new user with voiceprint."""
    data = request.json
    user_id = data.get('user_id')
    name = data.get('name')
    password = data.get('password')

    if User.query.filter_by(user_id=user_id).first():
        return jsonify({"message": "User ID already exists"}), 400

    hashed_password = generate_password_hash(password)
    new_user = User(user_id=user_id, name=name, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "User registered successfully"}), 201

@app.route('/login', methods=['POST'])
def login():
    """Authenticate a user."""
    data = request.json
    user_id = data.get('user_id')
    password = data.get('password')

    user = User.query.filter_by(user_id=user_id).first()
    if not user or not check_password_hash(user.password, password):
        return jsonify({"message": "Invalid credentials"}), 401

    return jsonify({"message": f"Welcome back, {user.name}!"}), 200

@app.route('/voice-auth', methods=['POST'])
def voice_auth():
    """Voice-based authentication."""
    data = request.json
    user_id = data.get('user_id')
    voice_sample = data.get('voice_sample')  # Base64 encoded voiceprint

    user = User.query.filter_by(user_id=user_id).first()
    if not user:
        return jsonify({"message": "User not found"}), 404

    # Compare voiceprint (dummy example)
    if user.voiceprint == voice_sample:
        return jsonify({"message": "Voice authentication successful!"}), 200
    return jsonify({"message": "Voice authentication failed!"}), 403

@app.route('/remote-control', methods=['POST'])
def remote_control():
    """Handle remote control commands."""
    data = request.json
    command_text = data.get('command', '').lower()

    if "turn on lights" in command_text:
        response_text = "Turning on the lights."
    elif "turn off lights" in command_text:
        response_text = "Turning off the lights."
    elif "lock the door" in command_text:
        response_text = "Locking the door."
    elif "unlock the door" in command_text:
        response_text = "Unlocking the door."
    else:
        response_text = "Command not recognized for remote control."

    # Emit real-time response
    socketio.emit('remote_control_response', {"response": response_text})
    return jsonify({"response": response_text})

@app.route('/save-voiceprint', methods=['POST'])
def save_voiceprint():
    """Save a user's voiceprint for authentication."""
    data = request.json
    user_id = data.get('user_id')
    voice_sample = data.get('voice_sample')  # Base64 encoded voice sample

    user = User.query.filter_by(user_id=user_id).first()
    if not user:
        return jsonify({"message": "User not found"}), 404

    user.voiceprint = voice_sample
    db.session.commit()
    return jsonify({"message": "Voiceprint saved successfully!"}), 200

@app.route('/generate-response', methods=['POST'])
def generate_response():
    """Generate creative response for Saliver."""
    commands = ["Tell me a joke", "Inspire me", "Play a song"]
    creative_response = random.choice(commands)
    engine.say(f"Here's a creative response: {creative_response}")
    engine.runAndWait()
    return jsonify({"response": creative_response}), 200

# Run Flask App
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True)

