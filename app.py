from flask import Flask, render_template_string, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_, and_
import os, uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-secret-key-for-club'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///club.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    bio = db.Column(db.String(255), default="")
    profile_pic = db.Column(db.String(255), default="default.png")

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=True)
    media = db.Column(db.String(255), nullable=True)
    media_type = db.Column(db.String(20), nullable=True)
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
    content = db.Column(db.Text, nullable=True)
    media = db.Column(db.String(255), nullable=True)
    media_type = db.Column(db.String(20), nullable=True)
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
        db.session.execute('ALTER TABLE message ADD COLUMN media VARCHAR(255)')
        db.session.execute('ALTER TABLE message ADD COLUMN media_type VARCHAR(20)')
        db.session.execute('ALTER TABLE post ADD COLUMN media VARCHAR(255)')
        db.session.execute('ALTER TABLE post ADD COLUMN media_type VARCHAR(20)')
        db.session.commit()
    except Exception:
        db.session.rollback()
        
    admin_user = User.query.filter_by(username='Aymn').first()
    if not admin_user:
        admin = User(username='Aymn', password_hash=generate_password_hash('9910'))
        db.session.add(admin)
        db.session.commit()

# التشكيلة (4-3-3 متباعدة)
LINEUPS = [
    {"name": "منذر", "position": "جناح أيسر", "number": 9, "top": "12%", "left": "15%"},
    {"name": "مصعب", "position": "رأس حربة", "number": 10, "top": "10%", "left": "50%"},
    {"name": "أيمن", "position": "جناح أيمن", "number": 7, "top": "12%", "left": "85%"},
    {"name": "محمد بلال", "position": "وسط أيسر", "number": 8, "top": "42%", "left": "15%"},
    {"name": "عباس", "position": "وسط مركزي", "number": 6, "top": "42%", "left": "50%"},
    {"name": "البخاري", "position": "وسط أيمن", "number": 14, "top": "42%", "left": "85%"},
    {"name": "عبدالرحمن", "position": "ظهير أيسر", "number": 3, "top": "72%", "left": "15%"},
    {"name": "محمد", "position": "قلب دفاع", "number": 4, "top": "72%", "left": "38%"},
    {"name": "أحمد", "position": "قلب دفاع", "number": 5, "top": "72%", "left": "62%"},
    {"name": "محمد", "position": "ظهير أيمن", "number": 2, "top": "72%", "left": "85%"},
    {"name": "النذير", "position": "الحارس", "number": 1, "top": "92%", "left": "50%"},
]

BASE_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>نسور حجرودسالم</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800&display=swap" rel="stylesheet">
    <style>
        :root { --green-neon: #10b981; --gold-neon: #fbbf24; --bg-dark: #020617; --card-bg: rgba(15, 23, 42, 0.7); }
        body { font-family: 'Tajawal', sans-serif; background: var(--bg-dark) url('https://images.unsplash.com/photo-1519681393784-d120267933ba?q=80&w=2070&auto=format&fit=crop') no-repeat center center/cover; background-attachment: fixed; color: #e2e8f0; padding-bottom: 75px; min-height: 100vh; }
        .glass-panel { background: var(--card-bg); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.1); border-radius: 20px; box-shadow: 0 8px 32px 0 rgba(0,0,0,0.37); padding: 20px; margin-bottom: 15px; }
        .top-navbar { background: rgba(2,6,23,0.85); backdrop-filter: blur(10px); padding: 12px 20px; position: sticky; top: 0; z-index: 1000; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(16,185,129,0.3); }
        .top-navbar .brand { color: var(--gold-neon); font-weight: 800; font-size: 1.2rem; text-shadow: 0 0 10px rgba(251,191,36,0.5); }
        .bottom-nav { position: fixed; bottom: 0; left: 0; right: 0; background: rgba(2,6,23,0.95); backdrop-filter: blur(10px); display: flex; justify-content: space-around; padding: 10px 0; z-index: 1000; border-top: 1px solid rgba(16,185,129,0.3); }
        .bottom-nav a { color: #94a3b8; text-decoration: none; display: flex; flex-direction: column; align-items: center; font-size: 0.7rem; font-weight: 600; transition: 0.3s; }
        .bottom-nav a.active { color: var(--green-neon); text-shadow: 0 0 8px var(--green-neon); }
        .bottom-nav i { font-size: 1.4rem; margin-bottom: 4px; }
        .badge-notify { background-color: #ef4444; color: white; border-radius: 50%; padding: 2px 6px; font-size: 0.65rem; position: absolute; top: -6px; left: -8px; box-shadow: 0 0 10px #ef4444; }
        
        /* الملعب العريض */
        .pitch-wrapper { padding: 0; margin: 0; width: 100%; }
        .pitch-container { position: relative; width: 100vw; height: 70vh; background: repeating-linear-gradient(0deg, #2e7d32, #2e7d32 40px, #1b5e20 40px, #1b5e20 80px); border-top: 3px solid white; border-bottom: 3px solid white; overflow: hidden; }
        .pitch-container::before { content: ''; position: absolute; top: 50%; left: 0; right: 0; height: 3px; background: rgba(255,255,255,0.5); }
        .pitch-container::after { content: ''; position: absolute; top: 50%; left: 50%; width: 120px; height: 120px; border: 3px solid rgba(255,255,255,0.5); border-radius: 50%; transform: translate(-50%, -50%); }
        .penalty-box-top { position: absolute; top: 0; left: 50%; transform: translateX(-50%); width: 300px; height: 100px; border: 3px solid rgba(255,255,255,0.5); border-top: none; }
        .penalty-box-bottom { position: absolute; bottom: 0; left: 50%; transform: translateX(-50%); width: 300px; height: 100px; border: 3px solid rgba(255,255,255,0.5); border-bottom: none; }
        .player-node { position: absolute; transform: translate(-50%, -50%); text-align: center; display: flex; flex-direction: column; align-items: center; width: 80px; }
        .player-icon { background: #1e3a8a; color: white; width: 35px; height: 35px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 1rem; border: 2px solid white; margin-bottom: 2px; }
        .player-name { background: rgba(0,0,0,0.7); color: white; font-weight: 800; font-size: 0.7rem; padding: 2px 4px; border-radius: 3px; white-space: nowrap; }
        .player-pos { color: #fbbf24; font-weight: 700; font-size: 0.6rem; text-shadow: 1px 1px 1px black; }

        .form-control { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.2); color: white; }
        .form-control:focus { background: rgba(255,255,255,0.1); border-color: var(--green-neon); box-shadow: 0 0 10px rgba(16,185,129,0.3); color: white; }
        .form-control::placeholder { color: #94a3b8; }
        .btn-neon { background: var(--green-neon); color: #020617; font-weight: bold; box-shadow: 0 0 10px var(--green-neon); border: none; }
        .media-content { max-width: 100%; border-radius: 12px; margin-top: 10px; max-height: 400px; object-fit: contain; }
    </style>
</head>
<body>
    <div class="top-navbar">
        <div class="brand"><i class="fas fa-dove"></i> نسور حجرودسالم</div>
        {% if current_user.is_authenticated %}
            <div class="top-icons d-flex gap-3">
                <a href="/polls" class="text-white" title="التصويت"><i class="fas fa-poll"></i></a>
                <a href="/matches" class="text-white" title="المباريات"><i class="fas fa-calendar-alt"></i></a>
                <a href="/profile" class="text-white" title="حسابي"><i class="fas fa-user-circle"></i></a>
            </div>
        {% endif %}
    </div>

    <div class="container mt-3">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }} p-2 text-center" style="font-size:0.9rem; border-radius: 10px;">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
    </div>
    {% block content %}{% endblock %}

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
<div class="glass-panel text-center mt-5">
    <i class="fas fa-dove fa-4x" style="color: var(--gold-neon); margin-bottom: 20px;"></i>
    <h2 style="color: var(--green-neon);">نسور حجرودسالم</h2>
    <p class="text-light">أهلاً بك يا {{ current_user.username }}</p>
</div>
""")

LOGIN_PAGE = BASE_HTML.replace('{% block content %}{% endblock %}', """
<div class="glass-panel" style="max-width: 400px; margin: 50px auto;">
    <h3 class="text-center mb-4" style="color: var(--green-neon);">تسجيل الدخول</h3>
    <form method="POST">
        <div class="mb-3"><label class="form-label text-light">اسم المستخدم</label><input type="text" name="username" class="form-control" required></div>
        <div class="mb-3"><label class="form-label text-light">كلمة المرور</label><input type="password" name="password" class="form-control" required></div>
        <button type="submit" class="btn btn-neon w-100">دخول</button>
    </form>
    <p class="text-center mt-3"><a href="/register" class="text-decoration-none" style="color: var(--gold-neon);">ليس لديك حساب؟ سجل الآن</a></p>
</div>
""")

REGISTER_PAGE = BASE_HTML.replace('{% block content %}{% endblock %}', """
<div class="glass-panel" style="max-width: 400px; margin: 50px auto;">
    <h3 class="text-center mb-4" style="color: var(--green-neon);">إنشاء حساب جديد</h3>
    <form method="POST" enctype="multipart/form-data">
        <div class="mb-3"><label class="form-label text-light">اسم المستخدم</label><input type="text" name="username" class="form-control" required></div>
        <div class="mb-3"><label class="form-label text-light">كلمة المرور</label><input type="password" name="password" class="form-control" required></div>
        <div class="mb-3"><label class="form-label text-light">صورة الحساب (اختياري)</label><input type="file" name="profile_pic" class="form-control" accept="image/*"></div>
        <button type="submit" class="btn btn-neon w-100">تسجيل</button>
    </form>
    <p class="text-center mt-3"><a href="/login" class="text-decoration-none" style="color: var(--gold-neon);">لديك حساب؟ سجل دخولك</a></p>
</div>
""")

PLAYERS_HTML = BASE_HTML.replace('{% block content %}{% endblock %}', """
<div class="pitch-wrapper mt-3">
    <h4 class="text-center mb-2" style="color: var(--gold-neon); font-weight: 900; text-shadow: 0 0 15px rgba(251, 191, 36, 0.6);">تشكيلة فريق كرة قدم 4-3-3</h4>
    <div class="pitch-container">
        <div class="penalty-box-top"></div>
        <div class="penalty-box-bottom"></div>
        {% for player in lineups %}
        <div class="player-node" style="top: {{ player.top }}; left: {{ player.left }};">
            <div class="player-icon"><i class="fas fa-tshirt"></i></div>
            <div class="player-name">{{ player.name }}</div>
            <div class="player-pos">({{ player.position }})</div>
        </div>
        {% endfor %}
    </div>
</div>
""")

MATCHES_HTML = BASE_HTML.replace('{% block content %}{% endblock %}', """
<div class="container mt-3">
    <h4 class="text-center mb-3" style="color: var(--gold-neon);">📅 جدول المباريات</h4>
    <div class="glass-panel text-center mb-3">
        <span class="badge bg-success mb-2">منتهية</span>
        <h5 class="text-light">2026-10-20 | 16:30</h5>
        <div class="d-flex justify-content-between align-items-center mt-3">
            <span class="fw-bold text-light">نسور حجرودسالم</span>
            <span class="fw-bold fs-4 px-3 py-1" style="background: rgba(16,185,129,0.2); border: 1px solid var(--green-neon); border-radius: 8px; color: var(--green-neon);">3 - 0</span>
            <span class="fw-bold text-light">النيل أبورغيوه</span>
        </div>
    </div>
</div>
""")

FEED_HTML = BASE_HTML.replace('{% block content %}{% endblock %}', """
<div class="container mt-3">
    <div class="glass-panel mb-3">
        <form method="POST" enctype="multipart/form-data">
            <div class="d-flex align-items-center gap-2 mb-2">
                <input type="text" name="content" class="form-control" placeholder="ماذا يدور في ذهنك يا نسر؟" required style="border-radius: 20px;">
            </div>
            <div class="d-flex justify-content-between align-items-center mt-2 pt-2 border-top border-secondary">
                <label for="media" class="mb-0" style="cursor: pointer; color: var(--green-neon);"><i class="fas fa-image fa-lg"></i></label>
                <input type="file" name="media" id="media" class="d-none" accept="image/*,video/*">
                <button type="submit" class="btn btn-neon rounded-pill px-4">نشر</button>
            </div>
        </form>
    </div>

    {% for post in posts %}
    <div class="glass-panel">
        <div class="d-flex justify-content-between">
            <div class="d-flex align-items-center gap-2 mb-2">
                <a href="/user/{{ post.author }}" class="text-decoration-none fw-bold" style="color: var(--gold-neon);">{{ post.author }}</a>
                <small class="text-muted">{{ post.timestamp.strftime('%Y-%m-%d %H:%M') }}</small>
            </div>
        </div>
        {% if post.content %}<p class="fs-6 text-light">{{ post.content }}</p>{% endif %}
        {% if post.media %}
            {% if post.media_type == 'image' %}<img src="{{ url_for('static', filename='uploads/' + post.media) }}" class="media-content">
            {% elif post.media_type == 'video' %}<video controls class="media-content"><source src="{{ url_for('static', filename='uploads/' + post.media) }}"></video>{% endif %}
        {% endif %}
        
        <div class="d-flex justify-content-between mt-3 pt-2 border-top border-secondary">
            <a href="/like/{{ post.id }}" class="text-decoration-none {% if post.is_liked %}text-danger{% else %}text-light{% endif %}"><i class="fas fa-heart"></i> {{ post.likes_count }}</a>
            <span class="text-light"><i class="fas fa-comment"></i> {{ post.comments|length }}</span>
        </div>
        
        <div class="mt-2">
            {% for comment in post.comments %}
            <div class="text-light mb-1" style="font-size:0.85rem; background: rgba(255,255,255,0.05); padding: 5px; border-radius: 5px;"><strong>{{ comment.author }}:</strong> {{ comment.content }}</div>
            {% endfor %}
            <form action="/comment/{{ post.id }}" method="POST" class="d-flex mt-2">
                <input type="text" name="comment" class="form-control form-control-sm me-2" placeholder="اكتب تعليقاً..." required style="border-radius: 15px;">
                <button type="submit" class="btn btn-sm btn-neon" style="border-radius: 15px;">رد</button>
            </form>
        </div>
    </div>
    {% endfor %}
</div>
""")

POLLS_HTML = BASE_HTML.replace('{% block content %}{% endblock %}', """
<div class="container mt-3">
    {% if current_user.username == 'Aymn' %}
    <div class="glass-panel mb-3">
        <h5 style="color: var(--green-neon);">إنشاء تصويت جديد</h5>
        <form method="POST">
            <input type="text" name="question" class="form-control mb-2" placeholder="السؤال" required>
            <div class="row">
                <div class="col-6"><input type="text" name="option1" class="form-control mb-2" placeholder="الخيار الأول" required></div>
                <div class="col-6"><input type="text" name="option2" class="form-control mb-2" placeholder="الخيار الثاني" required></div>
            </div>
            <button type="submit" class="btn btn-neon w-100">إنشاء</button>
        </form>
    </div>
    {% endif %}
    {% for poll in polls %}
    <div class="glass-panel mb-3">
        <h5 class="fw-bold" style="color: var(--green-neon);">{{ poll.question }}</h5>
        <div class="row mt-3">
            <div class="col-6"><form action="/vote/{{ poll.id }}/1" method="POST"><button type="submit" class="btn btn-outline-success w-100">{{ poll.option1 }} ({{ poll.votes1 }})</button></form></div>
            <div class="col-6"><form action="/vote/{{ poll.id }}/2" method="POST"><button type="submit" class="btn btn-outline-primary w-100">{{ poll.option2 }} ({{ poll.votes2 }})</button></form></div>
        </div>
    </div>
    {% endfor %}
</div>
""")

PROFILE_HTML = BASE_HTML.replace('{% block content %}{% endblock %}', """
<div class="container mt-4">
    <div class="glass-panel text-center">
        {% if current_user.profile_pic != 'default.png' %}
            <img src="{{ url_for('static', filename='uploads/' + current_user.profile_pic) }}" class="rounded-circle mx-auto mb-3" style="width: 100px; height: 100px; object-fit:cover; border: 3px solid var(--green-neon);">
        {% else %}
            <div class="bg-secondary rounded-circle mx-auto mb-3 d-flex justify-content-center align-items-center" style="width: 100px; height: 100px; color: white; font-size: 2.5rem; font-weight: bold;">{{ current_user.username[0] }}</div>
        {% endif %}
        <h4 style="color: var(--green-neon);">{{ current_user.username }}</h4>
        <p class="text-light">{{ current_user.bio if current_user.bio else 'وصف الموقع الرسمي.' }}</p>
        <form method="POST" enctype="multipart/form-data" class="mt-4 text-start">
            <label class="form-label fw-bold text-light">الوصف</label>
            <input type="text" name="bio" class="form-control mb-3" value="{{ current_user.bio }}" placeholder="اكتب وصفاً...">
            <label class="form-label fw-bold text-light">اختيار ملف</label>
            <input type="file" name="profile_pic" class="form-control mb-3" accept="image/*">
            <button type="submit" class="btn btn-neon w-100">حفظ التعديلات</button>
        </form>
    </div>
</div>
""")

USER_PROFILE_HTML = BASE_HTML.replace('{% block content %}{% endblock %}', """
<div class="container mt-4">
    <div class="glass-panel text-center">
        {% if user.profile_pic != 'default.png' %}
            <img src="{{ url_for('static', filename='uploads/' + user.profile_pic) }}" class="rounded-circle mx-auto mb-3" style="width: 120px; height: 120px; object-fit:cover; border: 4px solid var(--green-neon);">
        {% else %}
            <div class="bg-secondary rounded-circle mx-auto mb-3 d-flex justify-content-center align-items-center" style="width: 120px; height: 120px; color: white; font-size: 3rem; font-weight: bold;">{{ user.username[0] }}</div>
        {% endif %}
        <h4 style="color: var(--green-neon);">{{ user.username }}</h4>
        <p class="text-light">{{ user.bio if user.bio else 'لا يوجد وصف.' }}</p>
        <a href="/new_chat/{{ user.username }}" class="btn btn-neon w-100"><i class="fas fa-comment"></i> مراسلة</a>
    </div>
    <h5 class="mt-4 mb-3" style="color: var(--green-neon);">منشورات {{ user.username }}</h5>
    {% for post in posts %}
    <div class="glass-panel">
        {% if post.content %}<p class="fs-6 text-light">{{ post.content }}</p>{% endif %}
        <small class="text-muted">{{ post.timestamp.strftime('%Y-%m-%d %H:%M') }}</small>
    </div>
    {% endfor %}
</div>
""")

MESSAGES_LIST_HTML = BASE_HTML.replace('{% block content %}{% endblock %}', """
<div class="container mt-3">
    <div class="glass-panel">
        <h5 class="mb-3 fw-bold" style="color: var(--green-neon);">المحادثات</h5>
        <form method="POST" action="/new_chat" class="d-flex gap-2 mb-4">
            <input type="text" name="receiver" class="form-control" placeholder="ابحث عن اسم المستخدم..." required style="border-radius: 20px;">
            <button type="submit" class="btn btn-neon rounded-circle"><i class="fas fa-search"></i></button>
        </form>
        {% for chat in chats %}
        <a href="/chat/{{ chat.username }}" class="d-flex align-items-center p-3 mb-2 text-decoration-none text-light" style="background: rgba(255,255,255,0.05); border-radius: 15px;">
            <div class="bg-secondary rounded-circle d-flex justify-content-center align-items-center me-3" style="width: 50px; height: 50px; color: white; font-weight: bold; font-size: 1.2rem;">{{ chat.username[0] }}</div>
            <div class="flex-grow-1">
                <h6 class="mb-0 fw-bold" style="color: var(--green-neon);">{{ chat.username }}</h6>
                <small class="text-muted">اضغط للمحادثة</small>
            </div>
            {% if chat.unread > 0 %}<span class="badge bg-danger rounded-pill">{{ chat.unread }}</span>{% endif %}
        </a>
        {% else %}
        <p class="text-muted text-center mt-3">لا توجد محادثات بعد.</p>
        {% endfor %}
    </div>
</div>
""")

CHAT_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>محادثة مع {{ other_user }}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Tajawal', sans-serif; margin: 0; padding: 0; height: 100vh; display: flex; flex-direction: column; background: url('https://images.unsplash.com/photo-1506318137071-a8e063b4bec0?q=80&w=2070&auto=format&fit=crop') no-repeat center center/cover; }
        .chat-header { background: rgba(2,6,23,0.6); backdrop-filter: blur(10px); color: white; padding: 10px 15px; display: flex; align-items: center; gap: 12px; border-bottom: 1px solid rgba(255,255,255,0.1); }
        .chat-header a { color: var(--green-neon); text-decoration: none; }
        .chat-messages { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; }
        .msg-bubble { max-width: 80%; padding: 10px 14px; border-radius: 15px; margin-bottom: 15px; font-size: 0.95rem; position: relative; backdrop-filter: blur(10px); }
        .msg-sent { background: rgba(16, 185, 129, 0.4); border: 1px solid var(--green-neon); color: white; align-self: flex-end; border-bottom-right-radius: 2px; }
        .msg-received { background: rgba(255, 255, 255, 0.15); border: 1px solid rgba(255,255,255,0.2); color: white; align-self: flex-start; border-bottom-left-radius: 2px; }
        .chat-input-area { background: rgba(2,6,23,0.7); backdrop-filter: blur(15px); padding: 10px 15px; border-top: 1px solid rgba(255,255,255,0.1); }
        .input-wrapper { display: flex; align-items: center; background: rgba(255,255,255,0.1); border-radius: 30px; padding: 5px 15px; border: 1px solid rgba(255,255,255,0.2); }
        .input-wrapper input { background: transparent; border: none; color: white; flex: 1; outline: none; }
        .input-wrapper input::placeholder { color: #94a3b8; }
        .icon-btn { background: transparent; border: none; color: var(--green-neon); font-size: 1.2rem; padding: 5px 10px; cursor: pointer; }
        .media-chat { max-width: 100%; border-radius: 8px; margin-top: 5px; }
    </style>
</head>
<body>
    <div class="chat-header">
        <a href="/messages"><i class="fas fa-arrow-right fa-lg"></i></a>
        <div class="bg-secondary rounded-circle d-flex justify-content-center align-items-center" style="width: 40px; height: 40px; color: white; font-weight: bold; border: 1px solid var(--green-neon);">{{ other_user[0] }}</div>
        <strong class="fs-5">{{ other_user }}</strong>
        <div class="ms-auto">
            <button class="icon-btn" onclick="alert('ميزة المكالمات الصوتية تحتاج خادم WebRTC (قيد التطوير)')"><i class="fas fa-phone"></i></button>
            <button class="icon-btn" onclick="alert('ميزة الفيديو قيد التطوير')"><i class="fas fa-video"></i></button>
        </div>
    </div>
    <div class="chat-messages">
        {% for msg in msgs %}
            {% if msg.sender == current_user.username %}
                <div class="msg-bubble msg-sent">
                    {% if msg.content %}{{ msg.content }}{% endif %}
                    {% if msg.media %}
                        {% if msg.media_type == 'image' %}<img src="{{ url_for('static', filename='uploads/' + msg.media) }}" class="media-chat">
                        {% elif msg.media_type == 'video' %}<video controls class="media-chat"><source src="{{ url_for('static', filename='uploads/' + msg.media) }}"></video>{% endif %}
                    {% endif %}
                    <div style="font-size:0.6rem; text-align:left; margin-top:5px; opacity:0.7;">{{ msg.timestamp.strftime('%H:%M') }} <i class="fas fa-check-double" style="color: #60a5fa;"></i></div>
                </div>
            {% else %}
                <div class="msg-bubble msg-received">
                    {% if msg.content %}{{ msg.content }}{% endif %}
                    {% if msg.media %}
                        {% if msg.media_type == 'image' %}<img src="{{ url_for('static', filename='uploads/' + msg.media) }}" class="media-chat">
                        {% elif msg.media_type == 'video' %}<video controls class="media-chat"><source src="{{ url_for('static', filename='uploads/' + msg.media) }}"></video>{% endif %}
                    {% endif %}
                    <div style="font-size:0.6rem; text-align:left; margin-top:5px; opacity:0.7;">{{ msg.timestamp.strftime('%H:%M') }}</div>
                </div>
            {% endif %}
        {% endfor %}
    </div>
    <div class="chat-input-area">
        <form action="/chat/{{ other_user }}" method="POST" enctype="multipart/form-data" class="d-flex align-items-center gap-2">
            <label for="chat-media" class="icon-btn mb-0" style="cursor: pointer;"><i class="fas fa-camera"></i></label>
            <input type="file" name="media" id="chat-media" class="d-none" accept="image/*,video/*" onchange="this.form.submit()">
            <div class="input-wrapper flex-grow-1">
                <button type="button" class="icon-btn" onclick="alert('جاري تسجيل الصوت... (محاكاة)')"><i class="fas fa-microphone"></i></button>
                <input type="text" name="content" placeholder="اكتب رسالة..." autocomplete="off">
                <button type="button" class="icon-btn"><i class="fas fa-smile"></i></button>
            </div>
            <button type="submit" class="btn rounded-circle" style="background: var(--green-neon); color: #020617; width: 45px; height: 45px; box-shadow: 0 0 10px var(--green-neon);"><i class="fas fa-paper-plane"></i></button>
        </form>
    </div>
</body>
</html>
"""

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
        content = request.form.get('content', '')
        media_file = request.files.get('media')
        media_name = None
        media_type = None
        if media_file and media_file.filename != '':
            ext = media_file.filename.split('.')[-1].lower()
            media_name = f"{uuid.uuid4().hex}.{ext}"
            media_file.save(os.path.join(app.config['UPLOAD_FOLDER'], media_name))
            media_type = 'video' if ext in ['mp4', 'mov', 'avi'] else 'image'
        if content or media_name:
            db.session.add(Post(author=current_user.username, content=content, media=media_name, media_type=media_type))
            db.session.commit()
        return redirect(url_for('feed'))

    posts = Post.query.order_by(Post.timestamp.desc()).all()
    for post in posts:
        post.likes_count = PostLike.query.filter_by(post_id=post.id).count()
        post.comments = Comment.query.filter_by(post_id=post.id).all()
        post.is_liked = PostLike.query.filter_by(post_id=post.id, username=current_user.username).first() is not None
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

@app.route('/user/<username>')
@login_required
def user_profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=username).order_by(Post.timestamp.desc()).all()
    return render_template_string(USER_PROFILE_HTML, user=user, posts=posts)

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

@app.route('/messages')
@login_required
def messages():
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

@app.route('/new_chat/<username>')
@login_required
def direct_chat(username):
    return redirect(url_for('chat', other_user=username))

@app.route('/chat/<other_user>', methods=['GET', 'POST'])
@login_required
def chat(other_user):
    if request.method == 'POST':
        content = request.form.get('content', '')
        media_file = request.files.get('media')
        media_name = None
        media_type = None
        if media_file and media_file.filename != '':
            ext = media_file.filename.split('.')[-1].lower()
            media_name = f"{uuid.uuid4().hex}.{ext}"
            media_file.save(os.path.join(app.config['UPLOAD_FOLDER'], media_name))
            media_type = 'video' if ext in ['mp4', 'mov', 'avi'] else 'image'
        if content or media_name:
            db.session.add(Message(sender=current_user.username, receiver=other_user, content=content, media=media_name, media_type=media_type))
            db.session.commit()
        return redirect(url_for('chat', other_user=other_user))
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
