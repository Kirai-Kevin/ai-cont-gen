import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import google.generativeai as genai
from dotenv import load_dotenv
from models import db, User
import random
import emoji

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
if not app.config['SECRET_KEY']:
    raise ValueError("No SECRET_KEY set for Flask application")

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')
if not app.config['SQLALCHEMY_DATABASE_URI']:
    raise ValueError("No DATABASE_URI set for Flask application")

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Configure the Gemini Pro model
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-pro')

def add_hashtags_and_emojis(text):
    words = text.split()
    hashtags = ['#awesome', '#amazing', '#cool', '#wow', '#love', '#fun', '#beautiful', '#happy']
    emojis = [':smile:', ':heart:', ':star:', ':fire:', ':thumbsup:', ':sunglasses:', ':rocket:', ':sparkles:']
    
    for i in range(min(3, len(words))):
        index = random.randint(0, len(words) - 1)
        words[index] = words[index] + ' ' + random.choice(hashtags)
    
    text = ' '.join(words)
    text += ' ' + ' '.join(random.sample(emojis, 3))
    
    return emoji.emojize(text, language='alias')

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user:
            flash('Username already exists')
        else:
            new_user = User(username=username, password=generate_password_hash(password, method='pbkdf2:sha256'))
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for('index'))
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/generate', methods=['POST'])
@login_required
def generate_content():
    data = request.json
    guidelines_type = data['guidelinesType']
    company_guidelines = data.get('companyGuidelines', '')
    target_audience = data['targetAudience']
    emotion = data['emotion']
    topic = data['topic']
    
    prompt = f"""
    Generate content about {topic} for {target_audience} with {emotion} emotion.
    Guidelines: {guidelines_type}
    {f'Company Guidelines: {company_guidelines}' if guidelines_type == 'Company Guidelines' else ''}
    Do not include asterisks in the output.
    """
    
    response = model.generate_content(prompt)
    creative_content = add_hashtags_and_emojis(response.text)
    return jsonify({"generated_content": creative_content})

@app.route('/moderate', methods=['POST'])
@login_required
def moderate_content():
    data = request.json
    content = data['content']
    guidelines_type = data['guidelinesType']
    company_guidelines = data.get('companyGuidelines', '')
    
    prompt = f"""
    Determine if the following content violates {guidelines_type}.
    {f'Company Guidelines: {company_guidelines}' if guidelines_type == 'Company Guidelines' else ''}
    Content: {content}
    Respond with 'Appropriate' or 'Inappropriate' followed by a brief explanation.
    If inappropriate, provide an alternative version that meets the guidelines.
    Do not include asterisks in the output.
    """
    
    response = model.generate_content(prompt)
    moderation_result = add_hashtags_and_emojis(response.text)
    return jsonify({"moderation_result": moderation_result})

@app.route('/multiple_posts', methods=['POST'])
@login_required
def multiple_posts():
    data = request.json
    idea = data['idea']
    num_posts = data['numPosts']
    
    prompt = f"Generate {num_posts} different social media posts based on this idea: {idea}. Do not include asterisks in the output."
    
    response = model.generate_content(prompt)
    creative_posts = add_hashtags_and_emojis(response.text)
    return jsonify({"multiple_posts": creative_posts})

@app.route('/personal_brand', methods=['POST'])
@login_required
def personal_brand():
    data = request.json
    platform = data['platform']
    niche = data['niche']
    
    prompt = f"Create content to grow a personal brand on {platform} in the {niche} niche. Do not include asterisks in the output."
    
    response = model.generate_content(prompt)
    creative_brand_content = add_hashtags_and_emojis(response.text)
    return jsonify({"personal_brand_content": creative_brand_content})

def create_tables():
    with app.app_context():
        db.create_all()

if __name__ == '__main__':
    create_tables()