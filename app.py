from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gamified_tasks.db'
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    points = db.Column(db.Integer, default=0)
    level = db.Column(db.Integer, default=1)
    streak = db.Column(db.Integer, default=0)
    last_task_date = db.Column(db.DateTime)
    tasks = db.relationship('Task', backref='user', lazy=True)
    badges = db.relationship('UserBadge', backref='user', lazy=True)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500))
    due_date = db.Column(db.DateTime)
    completed = db.Column(db.Boolean, default=False)
    points = db.Column(db.Integer, default=10)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    completion_date = db.Column(db.DateTime)

class Badge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200))
    requirement = db.Column(db.Integer)  # Points/Tasks needed
    badge_type = db.Column(db.String(50))  # 'points', 'tasks', 'streak'

class UserBadge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    badge_id = db.Column(db.Integer, db.ForeignKey('badge.id'), nullable=False)
    earned_date = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def check_streak(user):
    if user.last_task_date:
        yesterday = datetime.utcnow() - timedelta(days=1)
        if user.last_task_date.date() < yesterday.date():
            user.streak = 0
            db.session.commit()

def check_badges(user):
    # Points badges
    points_badges = Badge.query.filter_by(badge_type='points').all()
    for badge in points_badges:
        if user.points >= badge.requirement:
            if not UserBadge.query.filter_by(user_id=user.id, badge_id=badge.id).first():
                new_badge = UserBadge(user_id=user.id, badge_id=badge.id)
                db.session.add(new_badge)
    
    # Streak badges
    streak_badges = Badge.query.filter_by(badge_type='streak').all()
    for badge in streak_badges:
        if user.streak >= badge.requirement:
            if not UserBadge.query.filter_by(user_id=user.id, badge_id=badge.id).first():
                new_badge = UserBadge(user_id=user.id, badge_id=badge.id)
                db.session.add(new_badge)
    
    db.session.commit()

def calculate_level(points):
    return (points // 100) + 1

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/dashboard')
@login_required
def dashboard():
    check_streak(current_user)
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    badges = Badge.query.join(UserBadge).filter(UserBadge.user_id == current_user.id).all()
    # Calculate progress in increments of 25 for Bootstrap width classes
    points_progress = current_user.points % 100 if current_user.points else 0
    progress = round(points_progress / 25) * 25  # Round to nearest 25 (25, 50, 75, 100)
    return render_template('dashboard.html', tasks=tasks, badges=badges, progress=progress)

@app.route('/add_task', methods=['POST'])
@login_required
def add_task():
    title = request.form.get('title')
    description = request.form.get('description')
    due_date_str = request.form.get('due_date')
    due_date = datetime.strptime(due_date_str, '%Y-%m-%d') if due_date_str else None
    
    task = Task(
        title=title,
        description=description,
        due_date=due_date,
        user_id=current_user.id
    )
    db.session.add(task)
    db.session.commit()
    
    return redirect(url_for('dashboard'))

@app.route('/complete_task/<int:task_id>')
@login_required
def complete_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if not task.completed:
        task.completed = True
        task.completion_date = datetime.utcnow()
        current_user.points += task.points
        current_user.level = calculate_level(current_user.points)
        
        # Update streak
        if current_user.last_task_date:
            yesterday = datetime.utcnow() - timedelta(days=1)
            if current_user.last_task_date.date() >= yesterday.date():
                current_user.streak += 1
            else:
                current_user.streak = 1
        else:
            current_user.streak = 1
        
        current_user.last_task_date = datetime.utcnow()
        check_badges(current_user)
        db.session.commit()
    
    return redirect(url_for('dashboard'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
        
        user = User(
            username=username,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()
        
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

def init_db():
    with app.app_context():
        db.create_all()
        
        # Create default badges if they don't exist
        badges = [
            ('Beginner', 'Earn your first 100 points', 100, 'points'),
            ('Intermediate', 'Earn 500 points', 500, 'points'),
            ('Expert', 'Earn 1000 points', 1000, 'points'),
            ('Streak Master', 'Maintain a 7-day streak', 7, 'streak'),
            ('Streak Champion', 'Maintain a 30-day streak', 30, 'streak')
        ]
        
        for badge_data in badges:
            if not Badge.query.filter_by(name=badge_data[0]).first():
                badge = Badge(
                    name=badge_data[0],
                    description=badge_data[1],
                    requirement=badge_data[2],
                    badge_type=badge_data[3]
                )
                db.session.add(badge)
        
        db.session.commit()

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
