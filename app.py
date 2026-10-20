from flask import Flask, render_template_string, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy import or_, and_
import os, uuid

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
# نماذج قاعدة البيانات
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

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, nullable=False)
    author = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)

class PostLike(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, nullable=False)
    username = db.Column(db.String(100), nullable=False)

class Poll(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(255), nullable=False)
    option1 = db.Column(db.String(100), nullable=False)
    option2 = db.Column(db.String(100), nullable=False)
    votes1 = db.Column(db.Integer, default=0)
    votes2 = db.Column(db.Integer, default=0)

class PollVote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    poll_id = db.Column(db.Integer, nullable=False)
    username = db.Column(db.String(100), nullable=False)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(100), nullable=False)
    receiver = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    is_read = db.Column(db.Boolean, default=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()
    try:
        db.session.execute('ALTER TABLE user ADD COLUMN bio VARCHAR(255) DEFAULT ""')
        db.session.execute('ALTER TABLE user ADD COLUMN profile_pic VARCHAR(255) DEFAULT "default.png"')
        db.session.execute('ALTER TABLE message ADD COLUMN is_read BOOLEAN DEFAULT 0')
        db.session.commit()
    except Exception:
        db.session.rollback()
        
    admin_user = User.query.filter_by(username='Aymn').first()
    if not admin_user:
        admin = User(username='Aymn', password_hash=generate_password_hash('9910'))
        db.session.add(admin)
        db.session.commit()

LINEUPS = [
    {"name": "مندر", "number": 9, "top": "15%", "left": "25%"},
    {"name": "مصعب", "number": 9, "top": "12%", "left": "50%"},
    {"name": "أيمن", "number": 7, "top": "15%", "left": "75%"},
    {"name": "محمد بلال", "number": 8, "top": "40%", "left": "25%"},
    {"name": "عباس", "number": 10, "top": "42%", "left": "50%"},
    {"name": "البخاري", "number": 6, "top": "40%", "left": "75%"},
    {"name": "عبدالرحمن", "number": 3, "top": "65%", "left": "15%"},
    {"name": "محمد", "number": 4, "top": "70%", "left": "38%"},
    {"name": "أحمد", "number": 5, "top": "70%", "left": "62%"},
    {"name": "محمد", "number": 2, "top": "65%", "left": "85%"},
    {"name": "النذير", "number": 1, "top": "90%", "left": "50%"},
]

# ==========================================
# القوالب (HTML) - تصميم موبايل (فيسبوك + واتساب)
# ==========================================
BASE_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>نادي نسور حجرودسالم</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&display=swap" rel="stylesheet">
    <style>
        :root { --primary-color: #1e5631; --secondary-color: #d4af37; --bg-light: #f0f2f5; --fb-blue: #1877f2; --wa-green: #075e54; }
        body { font-family: 'Tajawal', sans-serif; background-color: var(--bg-light); padding-bottom: 70px; }
        
        /* شريط التنقل العلوي */
        .top-navbar { background-color: var(--primary-color); color: white; padding: 10px 15px; position: sticky; top: 0; z-index: 1000; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 5px rgba(0,0,0,0.2); }
        .top-navbar .brand { color: var(--secondary-color); font-weight: 900; font-size: 1.2rem; }
        
        /* الشريط السفلي (مثل فيسبوك) */
        .bottom-nav { position: fixed; bottom: 0; left: 0; right: 0; background: white; display: flex; justify-content: space-around; padding: 8px 0; box-shadow: 0 -2px 10px rgba(0,0,0,0.1); z-index: 1000; }
        .bottom-nav a { color: #65676b; text-decoration: none; display: flex; flex-direction: column; align-items: center; font-size: 0.75rem; position: relative; }
        .bottom-nav a.active { color: var(--fb-blue); }
        .bottom-nav i { font-size: 1.3rem; margin-bottom: 2px; }
        .badge-notify { background-color: #dc3545; color: white; border-radius: 50%; padding: 2px 6px; font-size: 0.65rem; position: absolute; top: -5px; left: 0; }

        /* الكروت */
        .post-card { background: white; border-radius: 10px; padding: 15px; margin-bottom: 10px; box-shadow: 0 1px 2px rgba(0,0,0,0.1); }
        .profile-pic { width: 40px; height: 40px; border-radius: 50%; object-fit: cover; border: 1px solid #ddd; }
        .auth-form { max-width: 400px; margin: 30px auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
        
        /* الملعب */
        .pitch-container { position: relative; width: 100%; max-width: 600px; margin: 0 auto; aspect-ratio: 2 / 3; background: repeating-linear-gradient(0deg, #4caf50, #4caf50 50px, #388e3c 50px, #388e3c 100px); border: 3px solid white; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.3); overflow: hidden; }
        .pitch-container::before { content: ''; position: absolute; top: 50%; left: 0; right: 0; height: 2px; background: rgba(255,255,255,0.5); }
        .pitch-container::after { content: ''; position: absolute; top: 50%; left: 50%; width: 80px; height: 80px; border: 2px solid rgba(255,255,255,0.5); border-radius: 50%; transform: translate(-50%, -50%); }
        .penalty-box-top { position: absolute; top: 0; left: 50%; transform: translateX(-50%); width: 250px; height: 100px; border: 2px solid rgba(255,255,255,0.5); border-top: none; }
        .penalty-box-bottom { position: absolute; bottom: 0; left: 50%; transform: translateX(-50%); width: 250px; height: 100px; border: 2px solid rgba(255,255,255,0.5); border-bottom: none; }
        .player-node { position: absolute; transform: translate(-50%, -50%); text-align: center; display: flex; flex-direction: column; align-items: center; width: 80px; }
        .player-circle { background: var(--primary-color); color: var(--secondary-color); width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 900; font-size: 1.1rem; border: 2px solid var(--secondary-color); box-shadow: 0 4px 8px rgba(0,0,0,0.4); margin-bottom: 5px; }
        .player-name { background: rgba(0,0,0,0.7); color: white; font-weight: 700; font-size: 0.8rem; padding: 2px 6px; border-radius: 5px; white-space: nowrap; }

        /* دردشة واتساب */
        .chat-container { display: flex; flex-direction: column; height: calc(100vh - 120px); background: #e5ddd5 url('https://user-images.githubusercontent.com/15075759/28719144-86dc0f70-73b1-11e7-911d-60d70fcded21.png'); }
        .chat-header { background: var(--wa-green); color: white; padding: 10px 15px; display: flex; align-items: center; gap: 10px; }
        .chat-messages { flex: 1; overflow-y: auto; padding: 15px; display: flex; flex-direction: column; }
        .msg-bubble { max-width: 80%; padding: 8px 12px; border-radius: 8px; margin-bottom: 10px; font-size: 0.95rem; position: relative; }
        .msg-sent { background: #dcf8c6; align-self: flex-end; border-top-right-radius: 0; }
        .msg-received { background: white; align-self: flex-start; border-top-left-radius: 0; }
        .chat-input { background: #f0f0f0; padding: 10px; display: flex; gap: 10px; align-items: center; }
    </style>
</head>
<body>

    <!-- الشريط العلوي -->
    <div class="top-navbar">
        <div class="brand">🦅 نسور حجرودسالم</div>
        {% if current_user.is_authenticated %}
            <a href="/profile" style="color:white; text-decoration:none;"><i class="fas fa-user-circle fa-lg"></i></a>
        {% endif %}
    </div>

    <!-- المحتوى -->
    <div class="container mt-3">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }} p-2 text-center" style="font-size:0.9rem;">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
    </div>
    {% block content %}{% endblock %}

    <!-- الشريط السفلي (مثل فيسبوك) -->
    {% if current_user.is_authenticated %}
    <div class="bottom-nav">
        <a href="/" class="{% if request.path == '/' %}active{% endif %}"><i class="fas fa-home"></i> الرئيسية</a>
        <a href="/feed" class="{% if request.path == '/feed' %}active{% endif %}"><i class="fas fa-newspaper"></i> المنشورات</a>
        <a href="/players" class="{% if request.path == '/players' %}active{% endif %}"><i class="fas fa-users"></i> التشكيلة</a>
        <a href="/messages" class="{% if request.path == '/messages' %}active{% endif %}">
            <i class="fas fa-comment-dots"></i> الرسائل
            {% if unread_count > 0 %}<span class="badge-notify">{{ unread_count }}</span>{% endif %}
        </a>
        <a href="/logout" class="{% if request.path == '/logout' %}active{% endif %}"><i class="fas fa-sign-out-alt"></i> خروج</a>
    </div>
    {% endif %}

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

INDEX_HTML = BASE_HTML.replace('{% block content %}{% endblock %}', """
<div class="text-center mt-5">
    <h2 style="color: var(--primary-color); font-weight: 900;">أهلاً بك يا {{ current_user.username }}</h2>
    <p>هذا هو الموقع الرسمي للنادي.</p>
</div>
""")

LOGIN_PAGE = BASE_HTML.replace('{% block content %}{% endblock %}', """
<div class="auth-form">
    <h3 class="text-center mb-4" style="color: var(--primary-color);">تسجيل الدخول</h3>
    <form method="POST">
        <div class="mb-3"><label class="form-label">اسم المستخدم</label><input type="text" name="username" class="form-control" required></div>
        <div class="mb-3"><label class="form-label">كلمة المرور</label><input type="password" name="password" class="form-control" required></div>
        <button type="submit" class="btn w-100" style="background:var(--primary-color); color:white;">دخول</button>
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
        <button type="submit" class="btn w-100" style="background:var(--primary-color); color:white;">تسجيل</button>
    </form>
    <p class="text-center mt-3"><a href="/login">لديك حساب؟ سجل دخولك</a></p>
</div>
""")

PLAYERS_HTML = BASE_HTML.replace('{% block content %}{% endblock %}', """
<div class="container mt-4">
    <h4 class="text-center mb-3" style="color: var(--primary-color); font-weight: 900;">⭐ التشكيلة الأساسية ⭐</h4>
    <div class="pitch-container">
        <div class="penalty-box-top"></div>
        <div class="penalty-box-bottom"></div>
        {% for player in lineups %}
        <div class="player-node" style="top: {{ player.top }}; left: {{ player.left }};">
            <div class="player-circle">{{ player.number }}</div>
            <div class="player-name">{{ player.name }}</div>
        </div>
        {% endfor %}
    </div>
</div>
""")

MATCHES_HTML = BASE_HTML.replace('{% block content %}{% endblock %}', """
<div class="container mt-4">
    <h4 class="text-center mb-3" style="color: var(--primary-color); font-weight: 900;">📅 جدول المباريات</h4>
    <div class="post-card text-center">
        <span class="badge bg-info text-dark mb-2">قادمة</span>
        <h5>2026-11-01 | 17:00</h5>
        <div class="d-flex justify-content-between align-items-center mt-3">
            <span class="fw-bold">نسور حجرودسالم</span>
            <span class="text-warning fw-bold">VS</span>
            <span class="fw-bold">فريق الوحدة</span>
        </div>
    </div>
</div>
""")

# ===== المنشورات (مثل فيسبوك) =====
FEED_HTML = BASE_HTML.replace('{% block content %}{% endblock %}', """
<div class="container mt-3">
    <div class="post-card mb-3">
        <form method="POST" class="d-flex gap-2">
            <input type="text" name="content" class="form-control" placeholder="ماذا يدور في ذهنك يا نسر؟" required>
            <button type="submit" class="btn btn-primary" style="background:var(--fb-blue);">نشر</button>
        </form>
    </div>
    {% for post in posts %}
    <div class="post-card">
        <div class="d-flex align-items-center mb-2">
            <div class="bg-secondary rounded-circle d-flex justify-content-center align-items-center me-2" style="width: 40px; height: 40px; color: white; font-weight: bold;">{{ post.author[0] }}</div>
            <h6 class="mb-0 fw-bold">{{ post.author }}</h6>
        </div>
        <p class="fs-6">{{ post.content }}</p>
        <hr class="my-2">
        <div class="d-flex justify-content-between">
            <a href="/like/{{ post.id }}" class="btn btn-sm btn-light text-primary"><i class="fas fa-thumbs-up"></i> إعجاب ({{ post.likes_count }})</a>
            <span class="btn btn-sm btn-light text-muted"><i class="fas fa-comment"></i> تعليقات ({{ post.comments|length }})</span>
        </div>
        <div class="bg-light p-2 rounded mt-2">
            {% for comment in post.comments %}
            <div class="mb-1" style="font-size:0.9rem;"><strong>{{ comment.author }}:</strong> {{ comment.content }}</div>
            {% endfor %}
            <form action="/comment/{{ post.id }}" method="POST" class="mt-2 d-flex">
                <input type="text" name="comment" class="form-control form-control-sm me-2" placeholder="اكتب تعليقاً..." required>
                <button type="submit" class="btn btn-sm btn-primary" style="background:var(--fb-blue);">رد</button>
            </form>
        </div>
    </div>
    {% endfor %}
</div>
""")

POLLS_HTML = BASE_HTML.replace('{% block content %}{% endblock %}', """
<div class="container mt-4">
    {% if current_user.username == 'Aymn' %}
    <div class="post-card mb-3">
        <h5 style="color: var(--primary-color);">إنشاء تصويت جديد</h5>
        <form method="POST">
            <input type="text" name="question" class="form-control mb-2" placeholder="السؤال" required>
            <div class="row">
                <div class="col-6"><input type="text" name="option1" class="form-control mb-2" placeholder="الخيار الأول" required></div>
                <div class="col-6"><input type="text" name="option2" class="form-control mb-2" placeholder="الخيار الثاني" required></div>
            </div>
            <button type="submit" class="btn btn-gold w-100">إنشاء</button>
        </form>
    </div>
    {% endif %}
    {% for poll in polls %}
    <div class="post-card mb-3">
        <h5 class="fw-bold" style="color: var(--primary-color);">{{ poll.question }}</h5>
        <div class="row mt-3">
            <div class="col-6">
                <form action="/vote/{{ poll.id }}/1" method="POST">
                    <button type="submit" class="btn btn-outline-success w-100">{{ poll.option1 }} ({{ poll.votes1 }})</button>
                </form>
            </div>
            <div class="col-6">
                <form action="/vote/{{ poll.id }}/2" method="POST">
                    <button type="submit" class="btn btn-outline-primary w-100">{{ poll.option2 }} ({{ poll.votes2 }})</button>
                </form>
            </div>
        </div>
    </div>
    {% endfor %}
</div>
""")

PROFILE_HTML = BASE_HTML.replace('{% block content %}{% endblock %}', """
<div class="container mt-4">
    <div class="post-card text-center">
        {% if current_user.profile_pic != 'default.png' %}
            <img src="{{ url_for('static', filename='uploads/' + current_user.profile_pic) }}" class="rounded-circle mx-auto mb-3" style="width: 100px; height: 100px; object-fit:cover; border: 3px solid var(--fb-blue);">
        {% else %}
            <div class="bg-secondary rounded-circle mx-auto mb-3 d-flex justify-content-center align-items-center" style="width: 100px; height: 100px; color: white; font-size: 2.5rem; font-weight: bold;">{{ current_user.username[0] }}</div>
        {% endif %}
        <h4 style="color: var(--primary-color);">{{ current_user.username }}</h4>
        <p class="text-muted">{{ current_user.bio if current_user.bio else 'لا يوجد وصف بعد.' }}</p>
        <hr>
        <form method="POST" enctype="multipart/form-data">
            <input type="text" name="bio" class="form-control mb-2" value="{{ current_user.bio }}" placeholder="الوصف">
            <input type="file" name="profile_pic" class="form-control mb-2" accept="image/*">
            <button type="submit" class="btn btn-primary w-100" style="background:var(--fb-blue);">حفظ التعديلات</button>
        </form>
    </div>
</div>
""")

# ===== قائمة المحادثات (مثل واتساب) =====
MESSAGES_LIST_HTML = BASE_HTML.replace('{% block content %}{% endblock %}', """
<div class="container mt-3">
    <div class="post-card">
        <h5>المحادثات</h5>
        <form method="POST" action="/new_chat" class="d-flex gap-2 mb-3">
            <input type="text" name="receiver" class="form-control" placeholder="اسم المستخدم للمراسلة..." required>
            <button type="submit" class="btn btn-success" style="background:var(--wa-green);">بدء</button>
        </form>
        {% for chat in chats %}
        <a href="/chat/{{ chat.username }}" class="d-flex align-items-center p-2 border-bottom text-decoration-none text-dark">
            <div class="bg-secondary rounded-circle d-flex justify-content-center align-items-center me-2" style="width: 45px; height: 45px; color: white; font-weight: bold;">{{ chat.username[0] }}</div>
            <div class="flex-grow-1">
                <h6 class="mb-0 fw-bold">{{ chat.username }}</h6>
                <small class="text-muted">اضغط للمحادثة</small>
            </div>
            {% if chat.unread > 0 %}<span class="badge bg-success rounded-pill">{{ chat.unread }}</span>{% endif %}
        </a>
        {% else %}
        <p class="text-muted text-center">لا توجد محادثات بعد.</p>
        {% endfor %}
    </div>
</div>
""")

# ===== صفحة الدردشة (مثل واتساب) =====
CHAT_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>محادثة مع {{ other_user }}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Tajawal', sans-serif; background-color: #e5ddd5; margin: 0; padding: 0; height: 100vh; display: flex; flex-direction: column; }
        .chat-header { background: #075e54; color: white; padding: 10px 15px; display: flex; align-items: center; gap: 10px; }
        .chat-header a { color: white; text-decoration: none; }
        .chat-messages { flex: 1; overflow-y: auto; padding: 15px; display: flex; flex-direction: column; background-image: url('https://user-images.githubusercontent.com/15075759/28719144-86dc0f70-73b1-11e7-911d-60d70fcded21.png'); }
        .msg-bubble { max-width: 80%; padding: 8px 12px; border-radius: 8px; margin-bottom: 10px; font-size: 0.95rem; position: relative; box-shadow: 0 1px 1px rgba(0,0,0,0.1); }
        .msg-sent { background: #dcf8c6; align-self: flex-end; border-top-right-radius: 0; }
        .msg-received { background: white; align-self: flex-start; border-top-left-radius: 0; }
        .chat-input { background: #f0f0f0; padding: 10px; display: flex; gap: 10px; align-items: center; }
    </style>
</head>
<body>
    <div class="chat-header">
        <a href="/messages"><i class="fas fa-arrow-right"></i></a>
        <div class="bg-light rounded-circle d-flex justify-content-center align-items-center" style="width: 40px; height: 40px; color: #075e54; font-weight: bold;">{{ other_user[0] }}</div>
        <strong>{{ other_user }}</strong>
    </div>
    <div class="chat-messages">
        {% for msg in msgs %}
            {% if msg.sender == current_user.username %}
                <div class="msg-bubble msg-sent">{{ msg.content }}</div>
            {% else %}
                <div class="msg-bubble msg-received">{{ msg.content }}</div>
            {% endif %}
        {% endfor %}
    </div>
    <form action="/chat/{{ other_user }}" method="POST" class="chat-input">
        <input type="text" name="content" class="form-control rounded-pill" placeholder="اكتب رسالة..." required autocomplete="off">
        <button type="submit" class="btn btn-success rounded-circle" style="background:#075e54;"><i class="fas fa-paper-plane"></i></button>
    </form>
</body>
</html>
"""

# ==========================================
# المسارات
# ==========================================
@app.context_processor
def inject_unread_count():
    if current_user.is_authenticated:
        count = Message.query.filter_by(receiver=current_user.username, is_read=False).count()
        return dict(unread_count=count)
    return dict(unread_count=0)

@app.route('/')
@login_required
def home(): return render_template_string(INDEX_HTML)

@app.route('/players')
@login_required
def players(): return render_template_string(PLAYERS_HTML, lineups=LINEUPS)

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
        return redirect(url_for('feed'))
    posts = Post.query.order_by(Post.timestamp.desc()).all()
    for post in posts:
        post.likes_count = PostLike.query.filter_by(post_id=post.id).count()
        post.comments = Comment.query.filter_by(post_id=post.id).all()
    return render_template_string(FEED_HTML, posts=posts)

@app.route('/like/<int:post_id>')
@login_required
def like_post(post_id):
    if not PostLike.query.filter_by(post_id=post_id, username=current_user.username).first():
        db.session.add(PostLike(post_id=post_id, username=current_user.username))
        db.session.commit()
    return redirect(url_for('feed'))

@app.route('/comment/<int:post_id>', methods=['POST'])
@login_required
def add_comment(post_id):
    db.session.add(Comment(post_id=post_id, author=current_user.username, content=request.form['comment']))
    db.session.commit()
    return redirect(url_for('feed'))

@app.route('/polls', methods=['GET', 'POST'])
@login_required
def polls():
    if request.method == 'POST' and current_user.username == 'Aymn':
        db.session.add(Poll(question=request.form['question'], option1=request.form['option1'], option2=request.form['option2']))
        db.session.commit()
        return redirect(url_for('polls'))
    return render_template_string(POLLS_HTML, polls=Poll.query.all())

@app.route('/vote/<int:poll_id>/<int:choice>', methods=['POST'])
@login_required
def vote(poll_id, choice):
    if PollVote.query.filter_by(poll_id=poll_id, username=current_user.username).first():
        flash('لقد صوت مسبقاً.', 'danger')
        return redirect(url_for('polls'))
    poll = Poll.query.get_or_404(poll_id)
    if choice == 1: poll.votes1 += 1
    elif choice == 2: poll.votes2 += 1
    db.session.add(PollVote(poll_id=poll_id, username=current_user.username))
    db.session.commit()
    return redirect(url_for('polls'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.bio = request.form['bio']
        if 'profile_pic' in request.files:
            file = request.files['profile_pic']
            if file and file.filename != '':
                filename = f"{uuid.uuid4().hex}.{file.filename.split('.')[-1]}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                current_user.profile_pic = filename
        db.session.commit()
        return redirect(url_for('profile'))
    return render_template_string(PROFILE_HTML)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password_hash, request.form['password']):
            login_user(user)
            return redirect(url_for('home'))
        flash('خطأ في البيانات', 'danger')
    return render_template_string(LOGIN_PAGE)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if User.query.filter_by(username=request.form['username']).first():
            flash('الاسم موجود', 'danger')
            return redirect(url_for('register'))
        new_user = User(username=request.form['username'], password_hash=generate_password_hash(request.form['password']))
        if 'profile_pic' in request.files:
            file = request.files['profile_pic']
            if file and file.filename != '':
                filename = f"{uuid.uuid4().hex}.{file.filename.split('.')[-1]}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                new_user.profile_pic = filename
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template_string(REGISTER_PAGE)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# ===== مسارات الرسائل (واتساب) =====
@app.route('/messages')
@login_required
def messages():
    # جلب قائمة الأشخاص الذين لديهم محادثات
    all_msgs = Message.query.filter(or_(Message.sender == current_user.username, Message.receiver == current_user.username)).all()
    contacts = set()
    for m in all_msgs:
        if m.sender != current_user.username: contacts.add(m.sender)
        if m.receiver != current_user.username: contacts.add(m.receiver)
        
    chats = []
    for c in contacts:
        unread = Message.query.filter_by(sender=c, receiver=current_user.username, is_read=False).count()
        chats.append({"username": c, "unread": unread})
    return render_template_string(MESSAGES_LIST_HTML, chats=chats)

@app.route('/new_chat', methods=['POST'])
@login_required
def new_chat():
    receiver = request.form['receiver']
    if User.query.filter_by(username=receiver).first():
        return redirect(url_for('chat', other_user=receiver))
    flash('المستخدم غير موجود', 'danger')
    return redirect(url_for('messages'))

@app.route('/chat/<other_user>', methods=['GET', 'POST'])
@login_required
def chat(other_user):
    if request.method == 'POST':
        db.session.add(Message(sender=current_user.username, receiver=other_user, content=request.form['content']))
        db.session.commit()
        return redirect(url_for('chat', other_user=other_user))
    
    # تعليم الرسائل كمقروءة
    Message.query.filter_by(sender=other_user, receiver=current_user.username, is_read=False).update({"is_read": True})
    db.session.commit()
    
    msgs = Message.query.filter(or_(
        and_(Message.sender == current_user.username, Message.receiver == other_user),
        and_(Message.sender == other_user, Message.receiver == current_user.username)
    )).order_by(Message.timestamp.asc()).all()
    
    return render_template_string(CHAT_HTML, other_user=other_user, msgs=msgs)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
