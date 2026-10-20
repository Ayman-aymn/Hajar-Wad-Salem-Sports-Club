from flask import Flask, render_template_string, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-secret-key-for-club'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///club.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# ==========================================
# نماذج قاعدة البيانات (لن تتأثر بالكود الجديد)
# ==========================================
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    bio = db.Column(db.String(255), default="")
    profile_pic = db.Column(db.String(255), default="default.png")

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

class Poll(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(255), nullable=False)
    option1 = db.Column(db.String(100), nullable=False)
    option2 = db.Column(db.String(100), nullable=False)
    votes1 = db.Column(db.Integer, default=0)
    votes2 = db.Column(db.Integer, default=0)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()
    # الترقيع لإضافة الأعمدة الجديدة إذا كانت قاعدة البيانات قديمة
    try:
        db.session.execute('ALTER TABLE user ADD COLUMN bio VARCHAR(255) DEFAULT ""')
        db.session.execute('ALTER TABLE user ADD COLUMN profile_pic VARCHAR(255) DEFAULT "default.png"')
        db.session.commit()
    except Exception:
        db.session.rollback()
    if not User.query.first():
        admin = User(username='admin', password_hash=generate_password_hash('admin123'))
        db.session.add(admin)
        db.session.commit()

# ==========================================
# بيانات التشكيلة
# ==========================================
PLAYERS = [
    {"name": "النذير", "position": "حارس مرمى", "number": 1},
    {"name": "مصعب", "position": "مدافع", "number": 4},
    {"name": "مندر", "position": "مدافع", "number": 5},
    {"name": "أيمن", "position": "مدافع", "number": 3},
    {"name": "عباس", "position": "وسط", "number": 6},
    {"name": "محمد بلال", "position": "وسط", "number": 8},
    {"name": "البخاري", "position": "وسط", "number": 10},
    {"name": "احمد", "position": "وسط", "number": 14},
    {"name": "ود الشفيع", "position": "مهاجم", "number": 7},
    {"name": "محمد", "position": "مهاجم", "number": 9},
    {"name": "عبدالرحمن", "position": "مهاجم", "number": 11},
]

# ==========================================
# القوالب (HTML)
# ==========================================
BASE_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>نادي نسور حجرودسالم</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&display=swap" rel="stylesheet">
    <style>
        :root { --primary-color: #1e5631; --secondary-color: #d4af37; --bg-light: #f8f9fa; }
        body { font-family: 'Tajawal', sans-serif; background-color: var(--bg-light); }
        .navbar { background-color: var(--primary-color); box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .navbar-brand { color: var(--secondary-color) !important; font-weight: 900; }
        .nav-link { color: #fff !important; font-weight: 700; }
        .nav-link:hover { color: var(--secondary-color) !important; }
        .hero-section { background: linear-gradient(rgba(30, 86, 49, 0.8), rgba(30, 86, 49, 0.8)), url('https://images.unsplash.com/photo-1508098682722-e99c43a406b2?q=80&w=2070&auto=format&fit=crop') no-repeat center center/cover; color: white; padding: 80px 0; text-align: center; border-bottom: 5px solid var(--secondary-color); }
        .hero-title { font-size: 3rem; font-weight: 900; }
        .card-custom { border: none; border-radius: 15px; box-shadow: 0 10px 20px rgba(0,0,0,0.05); }
        .btn-gold { background-color: var(--secondary-color); color: var(--primary-color); font-weight: 900; }
        .btn-gold:hover { background-color: #b8960c; color: white; }
        .auth-form { max-width: 400px; margin: 50px auto; background: white; padding: 30px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); }
        footer { background-color: var(--primary-color); color: white; text-align: center; padding: 20px 0; margin-top: 50px; border-top: 4px solid var(--secondary-color); }
        .player-badge { background: linear-gradient(135deg, var(--primary-color), #2e7d32); color: white; border-radius: 20px; padding: 20px 10px; text-align: center; box-shadow: 0 5px 15px rgba(0,0,0,0.2); transition: transform 0.3s; border: 2px solid var(--secondary-color); }
        .player-badge:hover { transform: translateY(-5px); }
        .player-number-badge { background-color: var(--secondary-color); color: var(--primary-color); width: 50px; height: 50px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 1.5rem; font-weight: 900; margin: 0 auto 10px auto; }
        .post-card { background: white; border-radius: 15px; padding: 20px; margin-bottom: 20px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }
        .profile-pic { width: 50px; height: 50px; border-radius: 50%; object-fit: cover; border: 2px solid var(--secondary-color); }
        .poll-btn { width: 100%; margin-bottom: 10px; text-align: right; font-weight: bold; }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark">
        <div class="container">
            <a class="navbar-brand" href="/">🦅 نسور حجرودسالم</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav"><span class="navbar-toggler-icon"></span></button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ms-auto">
                    {% if current_user.is_authenticated %}
                        <li class="nav-item"><a class="nav-link" href="/">الرئيسية</a></li>
                        <li class="nav-item"><a class="nav-link" href="/players">التشكيلة</a></li>
                        <li class="nav-item"><a class="nav-link" href="/matches">المباريات</a></li>
                        <li class="nav-item"><a class="nav-link text-warning" href="/feed">المنشورات</a></li>
                        <li class="nav-item"><a class="nav-link text-warning" href="/polls">التصويت</a></li>
                        <li class="nav-item"><a class="nav-link text-warning" href="/messages">الرسائل</a></li>
                        <li class="nav-item"><a class="nav-link text-info" href="/profile">حسابي</a></li>
                        <li class="nav-item"><a class="nav-link text-danger" href="/logout">خروج</a></li>
                    {% else %}
                        <li class="nav-item"><a class="nav-link text-warning" href="/login">تسجيل الدخول</a></li>
                    {% endif %}
                </ul>
            </div>
        </div>
    </nav>
    <div class="container mt-3">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
    </div>
    {% block content %}{% endblock %}
    <footer><div class="container"><p class="mb-0">جميع الحقوق محفوظة &copy; 2026 - نادي نسور حجرودسالم</p></div></footer>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

# --- قوالب الصفحات المستقلة ---
INDEX_HTML = BASE_HTML.replace('{% block content %}{% endblock %}', """
<section class="hero-section">
    <div class="container">
        <h1 class="hero-title">مرحباً بك في نادي نسور حجرودسالم</h1>
        <p class="lead">حيث تلتقي الروح الرياضية بالطموح</p>
    </div>
</section>
<div class="container mt-5 text-center">
    <h2 style="color: var(--primary-color); font-weight: 900;">أهلاً بك يا {{ current_user.username }}</h2>
    <p>هذا هو الموقع الرسمي للنادي. تواصل مع الأعضاء، شاهد المنشورات، وشارك في التصويت.</p>
</div>
""")

LOGIN_PAGE = BASE_HTML.replace('{% block content %}{% endblock %}', """
<div class="auth-form">
    <h3 class="text-center mb-4" style="color: var(--primary-color);">تسجيل الدخول</h3>
    <form method="POST">
        <div class="mb-3"><label class="form-label">اسم المستخدم</label><input type="text" name="username" class="form-control" required></div>
        <div class="mb-3"><label class="form-label">كلمة المرور</label><input type="password" name="password" class="form-control" required></div>
        <button type="submit" class="btn btn-gold w-100">دخول</button>
    </form>
    <p class="text-center mt-3"><a href="/register">ليس لديك حساب؟ سجل الآن</a></p>
</div>
""")

REGISTER_PAGE = BASE_HTML.replace('{% block content %}{% endblock %}', """
<div class="auth-form">
    <h3 class="text-center mb-4" style="color: var(--primary-color);">إنشاء حساب جديد</h3>
    <form method="POST" enctype="multipart/form-data">
        <div class="mb-3"><label class="form-label">اسم المستخدم</label><input type="text" name="username" class="form-control" required></div>
        <div class="mb-3"><label class="form-label">كلمة المرور</label><input type="password" name="password" class="form-control" required></div>
        <div class="mb-3">
            <label class="form-label">صورة الحساب (اختياري)</label>
            <input type="file" name="profile_pic" class="form-control" accept="image/*">
        </div>
        <button type="submit" class="btn btn-gold w-100">تسجيل</button>
    </form>
    <p class="text-center mt-3"><a href="/login">لديك حساب؟ سجل دخولك</a></p>
</div>
""")

PLAYERS_HTML = BASE_HTML.replace('{% block content %}{% endblock %}', """
<div class="container mt-5">
    <h2 class="text-center mb-5" style="color: var(--primary-color); font-weight: 900;">⭐ التشكيلة الأساسية ⭐</h2>
    <div class="row g-4 justify-content-center">
        {% for player in players %}
        <div class="col-md-3 col-6">
            <div class="player-badge">
                <div class="player-number-badge">{{ player.number }}</div>
                <div class="player-name-text" style="font-size:1.3rem; font-weight:900;">{{ player.name }}</div>
                <div class="player-pos-text" style="color:#ddd; font-size:0.9rem;">{{ player.position }}</div>
            </div>
        </div>
        {% endfor %}
    </div>
</div>
""")

MATCHES_HTML = BASE_HTML.replace('{% block content %}{% endblock %}', """
<div class="container mt-5">
    <h2 class="text-center mb-5" style="color: var(--primary-color); font-weight: 900;">📅 جدول المباريات</h2>
    <div class="row g-4">
        <div class="col-md-6">
            <div class="card card-custom match-card p-4 text-center">
                <span class="badge bg-info text-dark mb-2">قادمة</span>
                <h5>2026-11-01 | 17:00</h5>
                <div class="d-flex justify-content-between align-items-center mt-3">
                    <span class="fs-4 fw-bold">نسور حجرودسالم</span>
                    <span class="fs-3 text-warning fw-bold">VS</span>
                    <span class="fs-4 fw-bold">فريق الوحدة</span>
                </div>
            </div>
        </div>
    </div>
</div>
""")

FEED_HTML = BASE_HTML.replace('{% block content %}{% endblock %}', """
<div class="container mt-5">
    <div class="row justify-content-center">
        <div class="col-md-8">
            <div class="post-card mb-4">
                <h4 style="color: var(--primary-color);">شاركنا رأيك</h4>
                <form method="POST">
                    <textarea name="content" class="form-control mb-2" rows="3" placeholder="ماذا يدور في ذهنك يا نسر؟" required></textarea>
                    <button type="submit" class="btn btn-gold w-100">نشر</button>
                </form>
            </div>
            <h3 class="mb-3" style="color: var(--primary-color);">📰 آخر المنشورات</h3>
            {% for post in posts %}
            <div class="post-card">
                <div class="d-flex align-items-center mb-2">
                    <div class="bg-secondary rounded-circle d-flex justify-content-center align-items-center me-2" style="width: 40px; height: 40px; color: white; font-weight: bold;">{{ post.author[0] }}</div>
                    <h6 class="mb-0 fw-bold">{{ post.author }}</h6>
                </div>
                <p class="fs-5">{{ post.content }}</p>
                <small class="text-muted">{{ post.timestamp.strftime('%Y-%m-%d %H:%M') }}</small>
            </div>
            {% else %}
            <p class="text-center text-muted">لا توجد منشورات بعد. كن أول من ينشر!</p>
            {% endfor %}
        </div>
    </div>
</div>
""")

POLLS_HTML = BASE_HTML.replace('{% block content %}{% endblock %}', """
<div class="container mt-5">
    <div class="row justify-content-center">
        <div class="col-md-8">
            <div class="post-card mb-4">
                <h4 style="color: var(--primary-color);">إنشاء تصويت جديد</h4>
                <form method="POST">
                    <input type="text" name="question" class="form-control mb-2" placeholder="السؤال (مثلاً: أفضل لاعب اليوم؟)" required>
                    <div class="row">
                        <div class="col-6"><input type="text" name="option1" class="form-control mb-2" placeholder="الخيار الأول" required></div>
                        <div class="col-6"><input type="text" name="option2" class="form-control mb-2" placeholder="الخيار الثاني" required></div>
                    </div>
                    <button type="submit" class="btn btn-gold w-100">إنشاء التصويت</button>
                </form>
            </div>
            <h3 class="mb-3" style="color: var(--primary-color);">🗳️ التصويتات النشطة</h3>
            {% for poll in polls %}
            <div class="post-card mb-3">
                <h5 class="fw-bold" style="color: var(--primary-color);">{{ poll.question }}</h5>
                <div class="row mt-3">
                    <div class="col-6">
                        <form action="/vote/{{ poll.id }}/1" method="POST">
                            <button type="submit" class="btn btn-outline-success poll-btn">{{ poll.option1 }} ({{ poll.votes1 }})</button>
                        </form>
                    </div>
                    <div class="col-6">
                        <form action="/vote/{{ poll.id }}/2" method="POST">
                            <button type="submit" class="btn btn-outline-primary poll-btn">{{ poll.option2 }} ({{ poll.votes2 }})</button>
                        </form>
                    </div>
                </div>
            </div>
            {% else %}
            <p class="text-center text-muted">لا توجد تصويتات نشطة.</p>
            {% endfor %}
        </div>
    </div>
</div>
""")

PROFILE_HTML = BASE_HTML.replace('{% block content %}{% endblock %}', """
<div class="container mt-5">
    <div class="row justify-content-center">
        <div class="col-md-6">
            <div class="post-card text-center">
                {% if current_user.profile_pic != 'default.png' %}
                    <img src="{{ url_for('static', filename='uploads/' + current_user.profile_pic) }}" class="profile-pic mx-auto mb-3" style="width: 120px; height: 120px;">
                {% else %}
                    <div class="bg-secondary rounded-circle mx-auto mb-3 d-flex justify-content-center align-items-center" style="width: 120px; height: 120px; color: white; font-size: 3rem; font-weight: bold;">{{ current_user.username[0] }}</div>
                {% endif %}
                <h3 style="color: var(--primary-color);">{{ current_user.username }}</h3>
                <p class="text-muted">{{ current_user.bio if current_user.bio else 'لا يوجد وصف بعد.' }}</p>
                <hr>
                <h5 class="text-start">تعديل الحساب</h5>
                <form method="POST" enctype="multipart/form-data">
                    <div class="mb-2 text-start">
                        <label class="form-label">الوصف (Bio)</label>
                        <input type="text" name="bio" class="form-control" value="{{ current_user.bio }}">
                    </div>
                    <div class="mb-3 text-start">
                        <label class="form-label">تغيير الصورة</label>
                        <input type="file" name="profile_pic" class="form-control" accept="image/*">
                    </div>
                    <button type="submit" class="btn btn-gold w-100">حفظ التعديلات</button>
                </form>
            </div>
        </div>
    </div>
</div>
""")

MESSAGES_HTML = BASE_HTML.replace('{% block content %}{% endblock %}', """
<div class="container mt-5">
    <h2 style="color: var(--primary-color);">📬 صندوق الرسائل</h2>
    <div class="row">
        <div class="col-md-4">
            <div class="card card-custom p-3">
                <h5>إرسال رسالة</h5>
                <form method="POST" action="/send_message">
                    <div class="mb-2"><input type="text" name="receiver" class="form-control" placeholder="إلى (اسم المستخدم)" required></div>
                    <div class="mb-2"><textarea name="content" class="form-control" placeholder="نص الرسالة..." rows="3" required></textarea></div>
                    <button type="submit" class="btn btn-gold w-100">إرسال</button>
                </form>
            </div>
        </div>
        <div class="col-md-8">
            <div class="card card-custom p-3">
                <h5>الرسائل الواردة</h5>
                {% for msg in messages %}
                    <div class="alert alert-info"><strong>{{ msg.sender }}:</strong> {{ msg.content }}</div>
                {% else %}
                    <p class="text-muted">لا توجد رسائل بعد.</p>
                {% endfor %}
            </div>
        </div>
    </div>
</div>
""")

# ==========================================
# المسارات
# ==========================================
@app.route('/')
@login_required
def home(): return render_template_string(INDEX_HTML)

@app.route('/players')
@login_required
def players(): return render_template_string(PLAYERS_HTML, players=PLAYERS)

@app.route('/matches')
@login_required
def matches(): return render_template_string(MATCHES_HTML)

@app.route('/feed', methods=['GET', 'POST'])
@login_required
def feed():
    if request.method == 'POST':
        new_post = Post(author=current_user.username, content=request.form['content'])
        db.session.add(new_post)
        db.session.commit()
        flash('تم نشر المنشور!', 'success')
        return redirect(url_for('feed'))
    posts = Post.query.order_by(Post.timestamp.desc()).all()
    return render_template_string(FEED_HTML, posts=posts)

@app.route('/polls', methods=['GET', 'POST'])
@login_required
def polls():
    if request.method == 'POST':
        new_poll = Poll(question=request.form['question'], option1=request.form['option1'], option2=request.form['option2'])
        db.session.add(new_poll)
        db.session.commit()
        flash('تم إنشاء التصويت!', 'success')
        return redirect(url_for('polls'))
    polls = Poll.query.all()
    return render_template_string(POLLS_HTML, polls=polls)

@app.route('/vote/<int:poll_id>/<int:choice>', methods=['POST'])
@login_required
def vote(poll_id, choice):
    poll = Poll.query.get_or_404(poll_id)
    if choice == 1: poll.votes1 += 1
    elif choice == 2: poll.votes2 += 1
    db.session.commit()
    flash('تم تسجيل صوتك!', 'success')
    return redirect(url_for('polls'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.bio = request.form['bio']
        if 'profile_pic' in request.files:
            file = request.files['profile_pic']
            if file and file.filename != '':
                ext = file.filename.split('.')[-1]
                filename = f"{uuid.uuid4().hex}.{ext}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                current_user.profile_pic = filename
        db.session.commit()
        flash('تم تحديث الحساب!', 'success')
        return redirect(url_for('profile'))
    return render_template_string(PROFILE_HTML)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated: return redirect(url_for('home'))
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password_hash, request.form['password']):
            login_user(user)
            return redirect(url_for('home'))
        flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'danger')
    return render_template_string(LOGIN_PAGE)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated: return redirect(url_for('home'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('اسم المستخدم موجود بالفعل', 'danger')
            return redirect(url_for('register'))
            
        # إنشاء المستخدم
        new_user = User(username=username, password_hash=generate_password_hash(password))
        
        # معالجة رفع الصورة (إذا وجدت)
        if 'profile_pic' in request.files:
            file = request.files['profile_pic']
            if file and file.filename != '':
                ext = file.filename.split('.')[-1]
                filename = f"{uuid.uuid4().hex}.{ext}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                new_user.profile_pic = filename

        db.session.add(new_user)
        db.session.commit()
        flash('تم إنشاء الحساب! سجل دخولك الآن.', 'success')
        return redirect(url_for('login'))
    return render_template_string(REGISTER_PAGE)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/messages')
@login_required
def messages():
    received = Message.query.filter_by(receiver=current_user.username).all()
    return render_template_string(MESSAGES_HTML, messages=received)

@app.route('/send_message', methods=['POST'])
@login_required
def send_message():
    receiver = request.form['receiver']
    content = request.form['content']
    if not User.query.filter_by(username=receiver).first():
        flash('المستخدم غير موجود', 'danger')
    else:
        new_msg = Message(sender=current_user.username, receiver=receiver, content=content)
        db.session.add(new_msg)
        db.session.commit()
        flash('تم إرسال الرسالة!', 'success')
    return redirect(url_for('messages'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
