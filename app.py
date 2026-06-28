import warnings
warnings.filterwarnings("ignore")

import razorpay
from flask import jsonify, request

# Initialize Razorpay Client with your exact keys
razorpay_client = razorpay.Client(auth=("rzp_test_SYeAmsoNC4GG0r", "knvMqsRp9mMy9mO0uU14pgYC"))

from flask import session, jsonify

import os
import random
import requests
import re
from datetime import datetime, timedelta

# --- FLASK IMPORTS ---
from flask import Flask, render_template, request, redirect, url_for, session, flash, make_response, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

# --- FLASK ADMIN IMPORTS ---
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_admin.menu import MenuLink

# --- DATA SCIENCE / PDF IMPORTS ---
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from fpdf import FPDF

# --- CONFIGURATION ---
app = Flask(__name__)
app.secret_key = 'ppsu_secret_key'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['FLASK_ADMIN_SWATCH'] = 'default'

UPLOAD_FOLDER = os.path.join('static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'ppsu_database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ========================================================
#             STRICT SESSION & CACHE MANAGEMENT
# ========================================================
@app.after_request
def add_header(response):
    # This completely disables browser caching. 
    # If a user logs out, they CANNOT use the back button or paste links to get back in.
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

# ========================================================
#                    DATABASE MODELS
# ========================================================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    fullname = db.Column(db.String(100), default="New Student")
    department = db.Column(db.String(50), default="General")
    profile_pic = db.Column(db.String(100), default="default.png")
    
    placement_status = db.Column(db.String(20), default="Pending")
    company_placed = db.Column(db.String(100), default="None")
    
    email = db.Column(db.String(150), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    languages = db.Column(db.String(200), nullable=True)
    degree = db.Column(db.String(100), nullable=True)
    major = db.Column(db.String(100), nullable=True)
    cgpa = db.Column(db.Float, nullable=True)
    github = db.Column(db.String(200), nullable=True)
    linkedin = db.Column(db.String(200), nullable=True)
    portfolio = db.Column(db.String(200), nullable=True)
    is_pro = db.Column(db.Boolean, default=False)
    grad_year = db.Column(db.String(10), default="2026") # ADDED SO THE DROPDOWN SAVES!


    def __str__(self):
        if self.fullname:
            return f"{self.username} ({self.fullname})"
        return self.username


class Prediction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='predictions')
    student_name = db.Column(db.String(100), nullable=True)
    company_name = db.Column(db.String(100), nullable=False)
    job_title = db.Column(db.String(150), nullable=False)
    score = db.Column(db.Float, nullable=False)
    date_predicted = db.Column(db.DateTime, default=datetime.utcnow)

class Notice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    category = db.Column(db.String(50), default="General")

class GeneratedResume(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='resumes')
    skills_included = db.Column(db.String(255), nullable=True)
    date_generated = db.Column(db.DateTime, default=datetime.utcnow)

class AssessmentRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='assessments')
    test_type = db.Column(db.String(100), nullable=False) 
    score = db.Column(db.Integer, nullable=True)
    total_questions = db.Column(db.Integer, nullable=True)
    date_taken = db.Column(db.DateTime, default=datetime.utcnow)


# ========================================================
#            ADMIN PANEL CONFIGURATION
# ========================================================

class SecureModelView(ModelView):
    def is_accessible(self):
        return 'user_role' in session and session['user_role'] == 'admin'
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login'))

class SecureAdminIndexView(AdminIndexView):
    def is_accessible(self):
        return 'user_role' in session and session['user_role'] == 'admin'

class UserModelView(SecureModelView):
    can_create = False  
    # FIXED: Added 'is_pro' and 'grad_year' so they show up in your Admin Interface!
    column_list = ['id', 'username', 'fullname', 'department', 'placement_status', 'company_placed', 'is_pro', 'grad_year']
    form_columns = ['username', 'fullname', 'password', 'role', 'department', 'placement_status', 'company_placed', 'email', 'phone', 'languages', 'degree', 'major', 'cgpa', 'grad_year', 'github', 'linkedin', 'portfolio', 'is_pro']

class PredictionAdminView(SecureModelView):
    column_list = ['id', 'user', 'company_name', 'job_title', 'score', 'date_predicted']
    form_columns = ['user', 'company_name', 'job_title', 'score', 'date_predicted']

class ResumeAdminView(SecureModelView):
    column_list = ['id', 'user', 'skills_included', 'date_generated']
    form_columns = ['user', 'skills_included', 'date_generated']

class AssessmentAdminView(SecureModelView):
    column_list = ['id', 'user', 'test_type', 'score', 'total_questions', 'date_taken']
    form_columns = ['user', 'test_type', 'score', 'total_questions', 'date_taken']

admin = Admin(app, name='Database Tools', template_mode='bootstrap3', index_view=SecureAdminIndexView())
admin.add_view(UserModelView(User, db.session)) 
admin.add_view(PredictionAdminView(Prediction, db.session))
admin.add_view(ResumeAdminView(GeneratedResume, db.session, name="Resumes"))
admin.add_view(AssessmentAdminView(AssessmentRecord, db.session, name="AI Tests"))
admin.add_view(SecureModelView(Notice, db.session))
admin.add_link(MenuLink(name='⬅ Back to Dashboard', category='', url='/admin_dashboard'))


# ========================================================
#            HELPERS & AI LOGIC / API
# ========================================================

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def clean_html(raw_html):
    cleanr = re.compile('<.*?>')
    return re.sub(cleanr, '', str(raw_html))[:250] + "..."

try:
    model = joblib.load('model/placement_model.pkl')
except:
    model = None

# ========================================================
#            REMOTIVE LIVE API FETCHING
# ========================================================

LIVE_JOBS_CACHE = {}

def fetch_live_jobs_and_notify():
    global LIVE_JOBS_CACHE
    try:
        # 100% WORKING REMOTIVE API
        url = "https://remotive.com/api/remote-jobs?category=software-dev&limit=20"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            api_jobs = response.json().get('jobs', [])
            latest_company = "Tech Corp"
            for j in api_jobs: 
                latest_company = j.get('company_name', 'Tech Startup')
                break 

            existing_notice = Notice.query.filter(Notice.title.like(f"%{latest_company}%")).first()
            if not existing_notice and latest_company != "Tech Corp":
                new_notice = Notice(title=f"🚨 Live API Alert: {latest_company} is Hiring!", content=f"Our live API detected new Software Engineering roles at {latest_company}.", category="Placement")
                db.session.add(new_notice)
                db.session.commit()
    except Exception as e:
        print(f"API Background Error: {e}")

# ========================================================
#            JOB PORTAL & PREDICTION
# ========================================================

@app.route('/jobs')
def job_portal():
    if 'user_role' not in session: return redirect(url_for('login'))
    global LIVE_JOBS_CACHE
    LIVE_JOBS_CACHE.clear() 
    try:
        url = "https://remotive.com/api/remote-jobs?category=software-dev&limit=20"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            api_jobs = response.json().get('jobs', [])
            
            for j in api_jobs:
                job_id = str(j.get('id', random.randint(1000, 9999)))
                raw_tags = j.get('tags', [])
                
                LIVE_JOBS_CACHE[job_id] = {
                    "id": job_id, 
                    "company": j.get('company_name', 'Tech Co'), 
                    "title": j.get('title', 'Software Engineer'),
                    "location": j.get('candidate_required_location', 'Remote'), 
                    "salary": j.get('salary', '') or "Undisclosed",
                    "type": j.get('job_type', 'Full Time').replace('_', ' ').title(), 
                    "posted": str(j.get('publication_date', ''))[:10],
                    "description": clean_html(j.get('description', '')), 
                    "url": j.get('url', '#'),
                    "reqs": raw_tags[:4] if raw_tags else ["Software", "Coding"]
                }
    except Exception as e: 
        print(f"Job Portal API Error: {e}")
        
    return render_template('jobs.html', jobs=list(LIVE_JOBS_CACHE.values()))

@app.route('/job/<job_id>')
def job_detail(job_id):
    if 'user_role' not in session: return redirect(url_for('login'))
    job = LIVE_JOBS_CACHE.get(job_id)
    if not job: return redirect(url_for('job_portal'))
    return render_template('job_detail.html', job=job)

@app.route('/predict_job/<job_id>', methods=['POST'])
def predict_job(job_id):
    job = LIVE_JOBS_CACHE.get(job_id)
    if request.method == 'POST' and job:
        try:
            cgpa = float(request.form['cgpa'])
            technical = float(request.form['technical'])
            aptitude = float(request.form['aptitude'])
            internships = int(request.form.get('internships', 0))
            backlogs = int(request.form.get('backlogs', 0))
            
            base_score = (cgpa * 4.5) + (aptitude * 0.15) + (technical * 2.5) + (internships * 3) - (backlogs * 8)
            final_prob = min(max(base_score, 0) + random.uniform(6.0, 11.0), 92.4) 

            user = User.query.get(session.get('user_id'))
            if user:
                new_prediction = Prediction(user_id=user.id, student_name=user.username, company_name=job['company'], job_title=job['title'], score=round(final_prob, 1))
                db.session.add(new_prediction)
                db.session.commit()

            msg = f"Strong Match! {final_prob:.1f}% likelihood." if final_prob > 75 else f"Fair Match. {final_prob:.1f}% likelihood."
            return render_template('job_detail.html', job=job, prediction_text=msg, result_class="success" if final_prob>75 else "warning", final_prob=round(final_prob,1))
        except Exception:
            return redirect(url_for('job_detail', job_id=job_id))
        

# ========================================================
#            Pro Plan ROUTES
# =======================================================

@app.route('/upgrade_to_pro', methods=['POST'])
def upgrade_to_pro():
    # Check if the user is logged in (adjust 'username' if your app uses 'id' or 'email' in the session)
    if 'username' in session: 
        # Find the user in the database
        user = User.query.filter_by(username=session['username']).first()
        
        if user:
            # Update database
            user.is_pro = True
            db.session.commit()
            
            # Also update the current session so the HTML updates instantly
            session['is_pro'] = True 
            
            return jsonify({"status": "success", "message": "Database updated to PRO!"})
            
    return jsonify({"status": "error", "message": "User not logged in"}), 401

# ========================================================
#            WEBSITE ROUTES
# ========================================================

@app.route('/')
def home():
    return render_template('index.html')

from werkzeug.security import check_password_hash

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # 1. Fetch user by username ONLY
        user = User.query.filter_by(username=username).first()
        
        # 2. Verify: Does user exist AND does the hash match the password?
        if user and check_password_hash(user.password, password):
            session.clear()
            session.permanent = True  
            session['user_role'] = user.role
            session['username'] = user.username
            session['user_id'] = user.id
            
            # 3. Role-based redirection
            if user.role == 'admin': 
                return redirect('/admin_dashboard')
            return redirect(url_for('dashboard'))
            
        # If either username or password is wrong
        flash('Invalid Username or Password', 'danger')
        
    return render_template('login.html')


from werkzeug.security import generate_password_hash
import re

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # 1. Password Strength Validation
        if len(password) < 8:
            flash('Password must be at least 8 characters long.', 'danger')
            return render_template('register.html')
            
        if not re.search(r"[A-Z]", password) or not re.search(r"[a-z]", password) or not re.search(r"[0-9]", password):
            flash('Password must contain upper, lower, and numbers.', 'danger')
            return render_template('register.html')

        # 2. Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Username is taken.', 'danger')
        else:
            # 3. HASH the password before storing it
            hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')
            new_user = User(username=username, password=hashed_pw, role='student')
            
            db.session.add(new_user)
            db.session.commit()
            
            flash('Account Created! Please Login.', 'success')
            return redirect(url_for('login'))
            
    return render_template('register.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    # 1. Check if the browser claims to be logged in
    if 'user_id' not in session: 
        return redirect(url_for('login'))
    
    # 2. Look up the user in the database
    user = User.query.get(session['user_id'])
    
    # 3. --- THE SAFETY NET ---
    # If the database says "Whoops, this user doesn't exist anymore!"
    if user is None:
        session.clear() # Destroy the ghost cookie
        return redirect(url_for('login')) # Kick them back to the login page
    # -------------------------

    # 4. If they passed the checks, run the rest of your normal code!
    fetch_live_jobs_and_notify()
    
    notices = Notice.query.order_by(Notice.date_posted.desc()).all()
    jobs_predicted = Prediction.query.filter_by(user_id=user.id).count()
    
    fields = [user.fullname, user.email, user.phone, user.cgpa, user.github, user.profile_pic != 'default.png']
    profile_score = int((sum(1 for f in fields if f) / len(fields)) * 100) if fields else 0

    return render_template('dashboard.html', user=user, role=session['user_role'], notices=notices, jobs_predicted=jobs_predicted, profile_score=profile_score)


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session: return redirect(url_for('login'))
    user = User.query.get(session['user_id'])

    if request.method == 'POST':
        if 'profile_pic' in request.files:
            file = request.files['profile_pic']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                unique_name = f"user_{user.id}_{filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_name))
                user.profile_pic = unique_name
        
        user.fullname = request.form.get('full_name', user.fullname)
        user.email = request.form.get('email', user.email)
        user.phone = request.form.get('phone', user.phone)
        user.languages = request.form.get('languages', user.languages)
        user.degree = request.form.get('degree', user.degree)
        user.major = request.form.get('major', user.major)
        user.grad_year = request.form.get('grad_year', user.grad_year) # FIXED: Actually saves the dropdown now!
        user.github = request.form.get('github', user.github)
        user.linkedin = request.form.get('linkedin', user.linkedin)
        user.portfolio = request.form.get('portfolio', user.portfolio)
        try:
            if request.form.get('cgpa'): user.cgpa = float(request.form.get('cgpa'))
        except ValueError: pass

        db.session.commit()
        flash('Profile updated!', 'success')
        return redirect(url_for('profile'))
    return render_template('profile.html', user=user)



# ========================================================
#            FULL AI QUESTION 
# ========================================================
QUESTIONS_DB = {
    'CSE': [
        {"q": "Which of these is NOT a valid variable name in Python?", "options": ["my_var", "_var", "2var", "var2"], "correct": "2var", "feedback": "Variable names cannot start with a number."},
        {"q": "What is the time complexity of binary search?", "options": ["O(n)", "O(log n)", "O(n^2)", "O(1)"], "correct": "O(log n)", "feedback": "Binary search divides the search interval in half each time."},
        {"q": "Which data structure is used for recursion?", "options": ["Queue", "Stack", "Linked List", "Tree"], "correct": "Stack", "feedback": "Recursion uses the call stack to keep track of function calls."},
        {"q": "What does ACID stand for in databases?", "options": ["Atomicity, Consistency, Isolation, Durability", "Automated, Consistent, Internal, Data", "Atomicity, Clarity, Integrity, Durability", "None"], "correct": "Atomicity, Consistency, Isolation, Durability", "feedback": "ACID properties ensure reliable database transactions."},
        {"q": "In Python, which keyword is used to start a function?", "options": ["func", "def", "function", "start"], "correct": "def", "feedback": "'def' is the keyword to define a function."},
        {"q": "What is 1 byte equal to?", "options": ["4 bits", "8 bits", "16 bits", "32 bits"], "correct": "8 bits", "feedback": "1 Byte = 8 Bits."},
        {"q": "Which sorting algorithm is the fastest on average?", "options": ["Bubble Sort", "Insertion Sort", "Quick Sort", "Selection Sort"], "correct": "Quick Sort", "feedback": "Quick Sort has an average case of O(n log n)."}
    ],
    'IT': [
         {"q": "What is Cloud Computing?", "options": ["Storing data on hard drive", "Delivery of computing services over internet", "Rain prediction", "None"], "correct": "Delivery of computing services over internet", "feedback": "Cloud computing delivers storage and power over the web."},
         {"q": "Full form of LAN?", "options": ["Local Area Network", "Long Area Network", "Live Area Network", "Local Access Network"], "correct": "Local Area Network", "feedback": "LAN connects computers within a limited area."},
         {"q": "Who owns AWS?", "options": ["Google", "Microsoft", "Amazon", "Apple"], "correct": "Amazon", "feedback": "AWS stands for Amazon Web Services."},
         {"q": "Which protocol sends email?", "options": ["HTTP", "FTP", "SMTP", "POP"], "correct": "SMTP", "feedback": "SMTP (Simple Mail Transfer Protocol) sends emails."},
         {"q": "What is a Firewall?", "options": ["A physical wall", "Network security system", "Virus", "Antivirus"], "correct": "Network security system", "feedback": "Firewalls monitor and control network traffic."}
    ],
    'HR': [
         {"q": "Tell me about yourself.", "options": ["I am [Name]", "I like cricket", "Professional summary & goals", "My family background"], "correct": "Professional summary & goals", "feedback": "Focus on your career, skills, and education."},
         {"q": "Why should we hire you?", "options": ["I need money", "I am the best", "I align with the job requirements", "I live nearby"], "correct": "I align with the job requirements", "feedback": "Match your skills to the company's needs."},
         {"q": "What is your weakness?", "options": ["I have none", "I work too hard", "Chocolate", "I get angry easily"], "correct": "I work too hard", "feedback": "Frame a weakness as a positive (e.g., perfectionism)."},
         {"q": "Where do you see yourself in 5 years?", "options": ["CEO", "Retired", "Growing in responsibility here", "Don't know"], "correct": "Growing in responsibility here", "feedback": "Show ambition aligned with the company."}
    ]
}

@app.route('/trainer', methods=['GET', 'POST'])
def trainer():
    if 'user_role' not in session: return redirect(url_for('login'))
    if 'quiz_score' not in session: session['quiz_score'] = 0
    if 'quiz_total' not in session: session['quiz_total'] = 0
    
    step, current_q, feedback_msg = 'mode_select', None, None
    
    if request.method == 'POST':
        if 'mode' in request.form:
            step = 'select_dept' if request.form['mode'] == 'quiz' else 'voice_start'
        
        elif 'department_selection' in request.form:
            session['current_dept'] = request.form['department_selection']
            session['quiz_score'], session['quiz_total'] = 0, 0
            step = 'quiz'
            current_q = random.choice(QUESTIONS_DB.get(session['current_dept'], QUESTIONS_DB['HR']))
        
        elif 'user_answer' in request.form: 
            step = 'result'
            session['quiz_total'] += 1
            if request.form['user_answer'] == request.form['correct_answer']:
                session['quiz_score'] += 1
                feedback_msg = {"status": "correct", "text": request.form.get('explanation', '')}
            else:
                feedback_msg = {"status": "wrong", "text": f"Incorrect. Right answer: {request.form['correct_answer']}. {request.form.get('explanation', '')}"}
            current_q = {"q": request.form['question_text']}

        elif 'next_question' in request.form:
            step = 'quiz'
            current_q = random.choice(QUESTIONS_DB.get(session.get('current_dept', 'HR'), QUESTIONS_DB['HR']))

        elif 'finish_quiz' in request.form:
            step = 'summary'
            new_test = AssessmentRecord(user_id=session['user_id'], test_type=f"{session.get('current_dept')} MCQ Test", score=session['quiz_score'], total_questions=session['quiz_total'])
            db.session.add(new_test)
            db.session.commit()

        elif 'start_voice' in request.form:
            step = 'voice_active'
            current_q = random.choice(QUESTIONS_DB['HR']) 

        elif 'voice_submit' in request.form:
            step = 'voice_feedback'
            current_q = {"q": request.form['question_text']}
            feedback_msg = request.form.get('model_answer', '') 
            
            new_interview = AssessmentRecord(user_id=session['user_id'], test_type="Voice Mock Interview")
            db.session.add(new_interview)
            db.session.commit()

        elif 'next_voice' in request.form:
            step = 'voice_active'
            current_q = random.choice(QUESTIONS_DB['HR'])

    return render_template('trainer.html', step=step, question=current_q, feedback=feedback_msg, dept=session.get('current_dept'), score=session.get('quiz_score'), total=session.get('quiz_total'))

# ========================================================
#            BUILD RESUME PDF ROUTE
# ========================================================

@app.route('/build_resume', methods=['GET', 'POST'])
def build_resume():
    if 'user_role' not in session: return redirect(url_for('login'))
    user = User.query.get(session['user_id'])

    if request.method == 'POST':
        skills = request.form.get('skills').split(',') 
        projects = request.form.get('projects')
        experience = request.form.get('experience')
        cgpa = request.form.get('cgpa')
        mobile = request.form.get('mobile')
        email = request.form.get('email')

        new_resume = GeneratedResume(user_id=user.id, skills_included=request.form.get('skills'))
        db.session.add(new_resume)
        db.session.commit()

        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=False) 

        pdf.set_fill_color(26, 44, 91) 
        pdf.rect(0, 0, 65, 297, 'F')  

        pdf.set_text_color(255, 255, 255)
        pdf.set_xy(5, 40)
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(55, 10, "CONTACT", 0, 1, 'L')
        
        pdf.set_draw_color(212, 175, 55) 
        pdf.set_line_width(0.5)
        pdf.line(5, 50, 50, 50)
        
        pdf.set_font("Arial", '', 9)
        pdf.set_xy(5, 55)
        pdf.multi_cell(55, 5, f"Phone:\n{mobile}\n\nEmail:\n{email}\n\nLocation:\nSurat, Gujarat", 0, 'L')

        pdf.set_xy(5, 110)  
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(55, 10, "EDUCATION", 0, 1, 'L')
        pdf.line(5, 120, 50, 120) 

        pdf.set_font("Arial", 'B', 10)
        pdf.set_xy(5, 125) 
        pdf.multi_cell(55, 5, user.degree or "Degree Pending", 0, 'L')
        
        pdf.set_font("Arial", '', 9)
        pdf.set_xy(5, 135) 
        pdf.multi_cell(55, 5, f"P. P. Savani University\nCGPA: {cgpa}\n(2025-2027)", 0, 'L')

        pdf.set_xy(5, 170) 
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(55, 10, "SKILLS", 0, 1, 'L')
        pdf.line(5, 180, 50, 180)
        
        pdf.set_font("Arial", '', 10)
        pdf.set_xy(5, 185)
        for skill in skills:
            pdf.cell(5, 5, "-", 0, 0)
            pdf.cell(50, 5, skill.strip(), 0, 1)

        pdf.set_text_color(26, 44, 91) 
        pdf.set_xy(75, 20)
        pdf.set_font("Arial", 'B', 28)
        pdf.cell(0, 15, user.fullname.upper(), 0, 1)
        
        pdf.set_text_color(100, 100, 100) 
        pdf.set_font("Arial", 'I', 14)
        pdf.set_xy(75, 35)
        pdf.cell(0, 10, f"Future {user.department} Professional", 0, 1)

        pdf.set_draw_color(212, 175, 55)
        pdf.set_line_width(1)
        pdf.line(75, 48, 200, 48)

        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", '', 10)
        pdf.set_xy(75, 55)
        pdf.multi_cell(0, 5, f"Motivated and detail-oriented student at P. P. Savani University with a strong foundation in {user.department} concepts. Passionate about leveraging technology to solve real-world problems. Seeking an entry-level position.")

        pdf.set_xy(75, 90)
        pdf.set_text_color(26, 44, 91) 
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "ACADEMIC PROJECTS", 0, 1)
        
        pdf.set_draw_color(200, 200, 200) 
        pdf.line(75, 100, 200, 100)
        
        pdf.set_text_color(0, 0, 0) 
        pdf.set_font("Arial", '', 11)
        pdf.set_xy(75, 105)
        pdf.multi_cell(0, 6, projects) 

        pdf.set_xy(75, 160) 
        pdf.set_text_color(26, 44, 91)
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "EXPERIENCE & CERTIFICATIONS", 0, 1)
        pdf.line(75, 170, 200, 170)
        
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", '', 11)
        pdf.set_xy(75, 175)
        pdf.multi_cell(0, 6, experience)

        response = make_response(pdf.output(dest='S').encode('latin-1'))
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename={user.username}_Resume.pdf'
        return response

    return render_template('resume_form.html', user=user)

# ========================================================
#            ADMIN DASHBOARD ROUTE
# ========================================================

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'user_role' not in session or session.get('user_role') != 'admin':
        return redirect(url_for('login'))
    
    total_students = User.query.filter_by(role='student').count()
    resumes_built = GeneratedResume.query.count()
    tests_taken = AssessmentRecord.query.count()
    predictions_made = Prediction.query.count()

    recent_users = User.query.filter_by(role='student').order_by(User.id.desc()).limit(3).all()
    recent_tests = AssessmentRecord.query.order_by(AssessmentRecord.id.desc()).limit(4).all()

    return render_template('admin_dashboard.html', 
                           total_students=total_students, 
                           resumes_built=resumes_built,
                           tests_taken=tests_taken,
                           predictions_made=predictions_made,
                           recent_users=recent_users,
                           recent_tests=recent_tests)


# ========================================================
#            RAZOR PAY API ROUTE
# ========================================================

@app.route('/create_order', methods=['POST'])
def create_order():
    try:
        # Amount is in PAISE. 499 INR = 49900 paise.
        order_amount = 49900 
        order_currency = 'INR'
        
        # Tell Razorpay to create an order
        razorpay_order = razorpay_client.order.create(dict(
            amount=order_amount,
            currency=order_currency,
            receipt='order_rcptid_11',
            payment_capture=1 # Auto-capture payment
        ))
        
        # Send the order ID back to our frontend
        return jsonify({
            'order_id': razorpay_order['id'],
            'amount': order_amount,
            'currency': order_currency
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    

@app.route('/premium_video')
def premium_video():
    # Only allow access if the user is logged in
    # In a real app, you'd check if session['tier'] == 'pro' here
    return render_template('premium_video.html')


@app.context_processor
def inject_admin_css():
    return dict(admin_css_file=url_for('static', filename='css/admin_custom.css'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='admin').first():
            db.session.add(User(username='admin', password='admin123', role='admin', fullname='Master Admin'))
            db.session.commit()
    app.run(debug=True)