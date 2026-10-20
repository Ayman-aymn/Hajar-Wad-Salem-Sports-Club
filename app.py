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

LINEUPS = [
    {"name": "منذر", "number": 9, "top": "15%", "left": "50%"},
    {"name": "مصعب", "number": 13, "top": "20%", "left": "25%"},
    {"name": "أيمن", "number": 18, "top": "20%", "left": "75%"},
    {"name": "البخاري", "number": 20, "top": "35%", "left": "50%"},
    {"name": "محمد بلال", "number": 24, "top": "45%", "left": "30%"},
    {"name": "عباس", "number": 8, "top": "45%", "left": "70%"},
    {"name": "محمد", "number": 1, "top": "55%", "left": "15%"},
    {"name": "عبدالرحمن", "number": 14, "top": "55%", "left": "50%"},
    {"name": "النذير", "number": 20, "top": "70%", "left": "50%"},
    {"name": "أحمد", "number": 13, "top": "65%", "left": "75%"},
    {"name": "محمد", "number": 1, "top": "65%", "left": "25%"},
]

# ==========================================
# القوالب (HTML) - تصميم احترافي يطابق الصورة
# ==========================================
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
        :root { 
            --primary: #0f172a; 
            --secondary: #d4af37; 
            --bg: #f1f5f9; 
            --card-bg: #ffffff;
            --green-dark: #064e3b;
            --green-light: #ecfdf5;
        }
        body { font-family: 'Tajawal', sans-serif; background-color: var(--bg); padding-bottom: 75px; color: #1e293b; }
        
        /* الشريط العلوي */
        .top-navbar { background: var(--green-dark); color: white; padding: 12px 20px; position: sticky; top: 0; z-index: 1000; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
        .top-navbar .brand { color: var(--secondary); font-weight: 800; font-size: 1.2rem; display: flex; align-items: center; gap: 8px; }
        .top-navbar .brand img { width: 30px; height: 30px; object-fit: contain; }
        
        /* الشريط السفلي */
        .bottom-nav { position: fixed; bottom: 0; left: 0; right: 0; background: white; display: flex; justify-content: space-around; padding: 10px 0; box-shadow: 0 -4px 15px rgba(0,0,0,0.05); z-index: 1000; border-top: 1px solid #e2e8f0; }
        .bottom-nav a { color: #64748b; text-decoration: none; display: flex; flex-direction: column; align-items: center; font-size: 0.7rem; font-weight: 600; position: relative; transition: 0.3s; }
        .bottom-nav a.active { color: var(--green-dark); }
        .bottom-nav i { font-size: 1.4rem; margin-bottom: 4px; }
        .badge-notify { background-color: #ef4444; color: white; border-radius: 50%; padding: 2px 6px; font-size: 0.65rem; position: absolute; top: -6px; left: -8px; box-shadow: 0 2px 4px rgba(0,0,0,0.2); }

        /* الكروت */
        .post-card { background: var(--card-bg); border-radius: 16px; padding: 20px; margin-bottom: 15px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); border: 1px solid #f1f5f9; }
        .profile-pic { width: 45px; height: 45px; border-radius: 50%; object-fit: cover; border: 2px solid #e2e8f0; }
        .media-content { max-width: 100%; border-radius: 12px; margin-top: 10px; max-height: 400px; object-fit: contain; }

        /* تصميم الملعب ثلاثي الأبعاد */
        .pitch-container { position: relative; width: 100%; max-width: 600px; margin: 0 auto; aspect-ratio: 16 / 10; background: #1e5631; border-radius: 10px; box-shadow: 0 20px 40px rgba(0,0,0,0.3); overflow: hidden; transform: perspective(800px) rotateX(20deg); margin-top: 20px; }
        .pitch-lines { position: absolute; top: 0; left: 0; right: 0; bottom: 0; border: 2px solid rgba(255,255,255,0.4); margin: 10px; border-radius: 5px; }
        .pitch-lines::before { content: ''; position: absolute; top: 50%; left: 0; right: 0; height: 2px; background: rgba(255,255,255,0.4); }
        .pitch-lines::after { content: ''; position: absolute; top: 50%; left: 50%; width: 60px; height: 60px; border: 2px solid rgba(255,255,255,0.4); border-radius: 50%; transform: translate(-50%, -50%); }
        .penalty-top { position: absolute; top: 10px; left: 50%; transform: translateX(-50%); width: 150px; height: 50px; border: 2px solid rgba(255,255,255,0.4); border-top: none; }
        .penalty-bottom { position: absolute; bottom: 10px; left: 50%; transform: translateX(-50%); width: 150px; height: 50px; border: 2px solid rgba(255,255,255,0.4); border-bottom: none; }
        
        .player-node { position: absolute; transform: translate(-50%, -50%); text-align: center; display: flex; flex-direction: column; align-items: center; width: 80px; }
        .player-circle { background: white; color: var(--green-dark); width: 35px; height: 35px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 900; font-size: 1rem; border: 2px solid #ddd; box-shadow: 0 4px 8px rgba(0,0,0,0.2); margin-bottom: 3px; }
        .player-name { background: rgba(0,0,0,0.7); color: white; font-weight: 700; font-size: 0.7rem; padding: 2px 6px; border-radius: 4px; white-space: nowrap; }

        /* دردشة واتساب */
        .chat-container { display: flex; flex-direction: column; height: calc(100vh - 130px); background: #efeae2 url('https://user-images.githubusercontent.com/15075759/28719144-86dc0f70-73b1-11e7-911d-60d70fcded21.png'); border-radius: 0 0 20px 20px; overflow: hidden; }
        .chat-header { background: var(--green-dark); color: white; padding: 12px 15px; display: flex; align-items: center; gap: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.2); z-index: 10; }
        .chat-messages { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; }
        .msg-bubble { max-width: 80%; padding: 10px 14px; border-radius: 12px; margin-bottom: 10px; font-size: 0.95rem; position: relative; box-shadow: 0 1px 2px rgba(0,0,0,0.1); }
        .msg-sent { background: #d9fdd3; align-self: flex-end; border-top-right-radius: 2px; }
        .msg-received { background: #ffffff; align-self: flex-start; border-top-left-radius: 2px; }
        .chat-input { background: #f0f2f5; padding: 10px 15px; display: flex; gap: 10px; align-items: center; }

        /* المنشورات */
        .post-actions { display: flex; justify-content: space-between; padding-top: 10px; border-top: 1px solid #f1f5f9; }
        .post-action-btn { color: #64748b; text-decoration: none; font-size: 0.9rem; font-weight: 600; display: flex; align-items: center; gap: 5px; }
        .post-action-btn:hover { color: var(--green-dark); }
        
        /* إشعار */
        .welcome-box { background: white; border-radius: 20px; padding: 40px 20px; text-align: center; margin-top: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.05); }
        .welcome-box img { width: 100px; margin-bottom: 20px; }
    </style>
</head>
<body>

    <!-- الشريط العلوي -->
    <div class="top-navbar">
        <div class="brand">
            <i class="fas fa-dove"></i> نسور حجرودسالم
        </div>
        {% if current_user.is_authenticated %}
            <div class="top-icons">
                <a href="/profile" class="text-white"><i class="fas fa-user-circle fa-lg"></i></a>
            </div>
        {% endif %}
    </div>

    <!-- المحتوى -->
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

    <!-- الشريط السفلي -->
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
<div class="welcome-box">
    <img src="https://cdn-icons-png.flaticon.com/512/40/40193.png" alt="Eagle">
    <h2 style="color: var(--green-dark); font-weight: 800;">نسور حجرودسالم</h2>
    <p class="text-muted">أهلاً بك يا {{ current_user.username }}</p>
    <p class="text-muted">هذا هو الموقع الرسمي للنادي.</p>
</div>
""")

LOGIN_PAGE = BASE_HTML.replace('{% block content %}{% endblock %}', """
<div class="post-card" style="max-width: 400px; margin: 50px auto; padding: 30px;">
    <h3 class="text-center mb-4" style="color: var(--green-dark); font-weight: 800;">تسجيل الدخول</h3>
    <form method="POST">
        <div class="mb-3"><label class="form-label">اسم المستخدم</label><input type="text" name="username" class="form-control" required></div>
        <div class="mb-3"><label class="form-label">كلمة المرور</label><input type="password" name="password" class="form-control" required></div>
        <button type="submit" class="btn w-100" style="background:var(--green-dark); color:white; font-weight: bold;">دخول</button>
    </form>
    <p class="text-center mt-3"><a href="/register" class="text-decoration-none">ليس لديك حساب؟ سجل الآن</a></p>
</div>
""")

REGISTER_PAGE = BASE_HTML.replace('{% block content %}{% endblock %}', """
<div class="post-card" style="max-width: 400px; margin: 50px auto; padding: 30px;">
    <h3 class="text-center mb-4" style="color: var(--green-dark); font-weight: 800;">إنشاء حساب جديد</h3>
    <form method="POST" enctype="multipart/form-data">
        <div class="mb-3"><label class="form-label">اسم المستخدم</label><input type="text" name="username" class="form-control" required></div>
        <div class="mb-3"><label class="form-label">كلمة المرور</label><input type="password" name="password" class="form-control" required></div>
        <div class="mb-3">
            <label class="form-label">صورة الحساب (اختياري)</label>
            <input type="file" name="profile_pic" class="form-control" accept="image/*">
        </div>
        <button type="submit" class="btn w-100" style="background:var(--green-dark); color:white; font-weight: bold;">تسجيل</button>
    </form>
    <p class="text-center mt-3"><a href="/login" class="text-decoration-none">لديك حساب؟ سجل دخولك</a></p>
</div>
""")

PLAYERS_HTML = BASE_HTML.replace('{% block content %}{% endblock %}', """
<div class="container mt-3">
    <h4 class="text-center mb-3" style="color: var(--green-dark); font-weight: 800;">⭐⭐⭐⭐⭐ التشكيلة الأساسية</h4>
    <div class="pitch-container">
        <div class="pitch-lines"></div>
        <div class="penalty-top"></div>
        <div class="penalty-bottom"></div>
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
<div class="container mt-3">
    <h4 class="text-center mb-3" style="color: var(--green-dark); font-weight: 800;">📅 جدول المباريات</h4>
    <div class="post-card text-center">
        <span class="badge bg-info text-dark mb-2">قادمة</span>
        <h5>2026-11-01 | 17:00</h5>
        <div class="d-flex justify-content-between align-items-center mt-3">
            <span class="fw-bold fs-5">نسور حجرودسالم</span>
            <span class="text-warning fw-bold fs-4">VS</span>
            <span class="fw-bold fs-5">فريق الوحدة</span>
        </div>
    </div>
</div>
""")

FEED_HTML = BASE_HTML.replace('{% block content %}{% endblock %}', """
<div class="container mt-3">
    <!-- نموذج النشر -->
    <div class="post-card mb-3">
        <form method="POST" enctype="multipart/form-data">
            <div class="d-flex align-items-center gap-2 mb-2">
                <div class="bg-secondary rounded-circle d-flex justify-content-center align-items-center" style="width: 40px; height: 40px; color: white;"><i class="fas fa-user"></i></div>
                <input type="text" name="content" class="form-control" placeholder="ماذا يدور في ذهنك يا نسر؟" required style="border-radius: 20px; background: #f1f5f9;">
            </div>
            <div class="d-flex justify-content-between align-items-center mt-2 border-top pt-2">
                <div class="d-flex gap-3">
                    <label for="media" class="text-success mb-0" style="cursor: pointer;"><i class="fas fa-image fa-lg"></i></label>
                    <input type="file" name="media" id="media" class="d-none" accept="image/*,video/*">
                </div>
                <button type="submit" class="btn btn-success rounded-pill px-4">نشر</button>
            </div>
        </form>
    </div>

    {% for post in posts %}
    <div class="post-card">
        <div class="d-flex justify-content-between">
            <div class="d-flex align-items-center gap-2 mb-2">
                {% if post.author_pic != 'default.png' %}
                <img src="{{ url_for('static', filename='uploads/' + post.author_pic) }}" class="profile-pic">
                {% else %}
                <div class="bg-secondary rounded-circle d-flex justify-content-center align-items-center" style="width: 45px; height: 45px; color: white; font-weight: bold;">{{ post.author[0] }}</div>
                {% endif %}
                <div>
                    <a href="/user/{{ post.author }}" class="text-decoration-none fw-bold" style="color: var(--green-dark);">{{ post.author }}</a>
                    <br><small class="text-muted">{{ post.timestamp.strftime('%Y-%m-%d %H:%M') }}</small>
                </div>
            </div>
            <i class="fas fa-ellipsis-h text-muted"></i>
        </div>
        
        {% if post.content %}<p class="fs-6 mt-2">{{ post.content }}</p>{% endif %}
        {% if post.media %}
            {% if post.media_type == 'image' %}<img src="{{ url_for('static', filename='uploads/' + post.media) }}" class="media-content">
            {% elif post.media_type == 'video' %}<video controls class="media-content"><source src="{{ url_for('static', filename='uploads/' + post.media) }}"></video>{% endif %}
        {% endif %}
        
        <div class="post-actions mt-3">
            <a href="/like/{{ post.id }}" class="post-action-btn {% if post.is_liked %}text-danger{% endif %}"><i class="fas fa-heart"></i> {{ post.likes_count }}</a>
            <span class="post-action-btn"><i class="fas fa-comment"></i> {{ post.comments|length }}</span>
            <span class="post-action-btn"><i class="fas fa-share"></i></span>
        </div>
    </div>
    {% endfor %}
</div>
""")

POLLS_HTML = BASE_HTML.replace('{% block content %}{% endblock %}', """
<div class="container mt-3">
    {% if current_user.username == 'Aymn' %}
    <div class="post-card mb-3">
        <h5 style="color: var(--green-dark); font-weight: 800;">إنشاء تصويت جديد</h5>
        <form method="POST">
            <input type="text" name="question" class="form-control mb-2" placeholder="السؤال (مثلاً: أفضل لاعب اليوم؟)" required style="border-radius: 10px;">
            <div class="row">
                <div class="col-6"><input type="text" name="option1" class="form-control mb-2" placeholder="الخيار الأول" required style="border-radius: 10px;"></div>
                <div class="col-6"><input type="text" name="option2" class="form-control mb-2" placeholder="الخيار الثاني" required style="border-radius: 10px;"></div>
            </div>
            <button type="submit" class="btn w-100" style="background:var(--green-dark); color:white; font-weight: bold;">إنشاء التصويت</button>
        </form>
    </div>
    {% endif %}
    {% for poll in polls %}
    <div class="post-card mb-3">
        <h5 class="fw-bold" style="color: var(--green-dark);">{{ poll.question }}</h5>
        <div class="row mt-3">
            <div class="col-6">
                <form action="/vote/{{ poll.id }}/1" method="POST">
                    <button type="submit" class="btn btn-outline-success w-100" style="border-radius: 10px;">{{ poll.option1 }} ({{ poll.votes1 }})</button>
                </form>
            </div>
            <div class="col-6">
                <form action="/vote/{{ poll.id }}/2" method="POST">
                    <button type="submit" class="btn btn-outline-primary w-100" style="border-radius: 10px;">{{ poll.option2 }} ({{ poll.votes2 }})</button>
                </form>
            </div>
        </div>
    </div>
    {% endfor %}
</div>
""")

PROFILE_HTML = BASE_HTML.replace('{% block content %}{% endblock %}', """
<div class="container mt-4">
    <div class="post-card text-center" style="border-radius: 20px;">
        {% if current_user.profile_pic != 'default.png' %}
            <img src="{{ url_for('static', filename='uploads/' + current_user.profile_pic) }}" class="rounded-circle mx-auto mb-3" style="width: 100px; height: 100px; object-fit:cover; border: 3px solid #e2e8f0;">
        {% else %}
            <div class="bg-secondary rounded-circle mx-auto mb-3 d-flex justify-content-center align-items-center" style="width: 100px; height: 100px; color: white; font-size: 2.5rem; font-weight: bold;">{{ current_user.username[0] }}</div>
        {% endif %}
        <h4 style="color: var(--green-dark); font-weight: 800;">{{ current_user.username }}</h4>
        <p class="text-muted" style="font-size:0.9rem;">{{ current_user.bio if current_user.bio else 'وصف الموقع الرسمي.' }}</p>
        
        <form method="POST" enctype="multipart/form-data" class="mt-4 text-start">
            <label class="form-label fw-bold">الوصف</label>
            <input type="text" name="bio" class="form-control mb-3" value="{{ current_user.bio }}" placeholder="اكتب وصفاً..." style="border-radius: 10px;">
            
            <label class="form-label fw-bold">اختيار ملف</label>
            <input type="file" name="profile_pic" class="form-control mb-3" accept="image/*" style="border-radius: 10px;">
            
            <button type="submit" class="btn w-100" style="background: #10b981; color:white; font-weight: bold; border-radius: 10px;">حفظ التعديلات</button>
        </form>
    </div>
</div>
""")

USER_PROFILE_HTML = BASE_HTML.replace('{% block content %}{% endblock %}', """
<div class="container mt-4">
    <div class="post-card text-center">
        {% if user.profile_pic != 'default.png' %}
            <img src="{{ url_for('static', filename='uploads/' + user.profile_pic) }}" class="rounded-circle mx-auto mb-3" style="width: 120px; height: 120px; object-fit:cover; border: 4px solid var(--green-dark);">
        {% else %}
            <div class="bg-secondary rounded-circle mx-auto mb-3 d-flex justify-content-center align-items-center" style="width: 120px; height: 120px; color: white; font-size: 3rem; font-weight: bold;">{{ user.username[0] }}</div>
        {% endif %}
        <h4 style="color: var(--green-dark); font-weight: 800;">{{ user.username }}</h4>
        <p class="text-muted">{{ user.bio if user.bio else 'لا يوجد وصف.' }}</p>
        <a href="/new_chat/{{ user.username }}" class="btn btn-success w-100" style="background:var(--green-dark); border-radius: 10px;"><i class="fas fa-comment"></i> مراسلة</a>
    </div>
    
    <h5 class="mt-4 mb-3" style="color: var(--green-dark); font-weight: 800;">منشورات {{ user.username }}</h5>
    {% for post in posts %}
    <div class="post-card">
        {% if post.content %}<p class="fs-6">{{ post.content }}</p>{% endif %}
        {% if post.media %}
            {% if post.media_type == 'image' %}<img src="{{ url_for('static', filename='uploads/' + post.media) }}" class="media-content">
            {% elif post.media_type == 'video' %}<video controls class="media-content"><source src="{{ url_for('static', filename='uploads/' + post.media) }}"></video>{% endif %}
        {% endif %}
        <small class="text-muted">{{ post.timestamp.strftime('%Y-%m-%d %H:%M') }}</small>
    </div>
    {% else %}
    <p class="text-muted text-center">لا توجد منشورات لهذا المستخدم.</p>
    {% endfor %}
</div>
""")

MESSAGES_LIST_HTML = BASE_HTML.replace('{% block content %}{% endblock %}', """
<div class="container mt-3">
    <div class="post-card" style="border-radius: 20px;">
        <h5 class="mb-3 fw-bold" style="color: var(--green-dark);">المحادثات</h5>
        <form method="POST" action="/new_chat" class="d-flex gap-2 mb-4">
            <input type="text" name="receiver" class="form-control" placeholder="ابحث عن اسم المستخدم..." required style="border-radius: 20px; background: #f1f5f9;">
            <button type="submit" class="btn btn-success rounded-circle" style="background:var(--green-dark); width: 45px; height: 45px;"><i class="fas fa-search"></i></button>
        </form>
        {% for chat in chats %}
        <a href="/chat/{{ chat.username }}" class="d-flex align-items-center p-3 mb-2 text-decoration-none text-dark" style="background: #f8fafc; border-radius: 15px;">
            <div class="bg-secondary rounded-circle d-flex justify-content-center align-items-center me-3" style="width: 50px; height: 50px; color: white; font-weight: bold; font-size: 1.2rem;">{{ chat.username[0] }}</div>
            <div class="flex-grow-1">
                <h6 class="mb-0 fw-bold" style="color: var(--green-dark);">{{ chat.username }}</h6>
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
        body { font-family: 'Tajawal', sans-serif; background-color: #efeae2; margin: 0; padding: 0; height: 100vh; display: flex; flex-direction: column; }
        .chat-header { background: #064e3b; color: white; padding: 10px 15px; display: flex; align-items: center; gap: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.2); z-index: 10; }
        .chat-header a { color: white; text-decoration: none; }
        .chat-messages { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; background-image: url('https://user-images.githubusercontent.com/15075759/28719144-86dc0f70-73b1-11e7-911d-60d70fcded21.png'); }
        .msg-bubble { max-width: 80%; padding: 10px 14px; border-radius: 12px; margin-bottom: 10px; font-size: 0.95rem; position: relative; box-shadow: 0 1px 2px rgba(0,0,0,0.1); }
        .msg-sent { background: #d9fdd3; align-self: flex-end; border-top-right-radius: 2px; }
        .msg-received { background: #ffffff; align-self: flex-start; border-top-left-radius: 2px; }
        .chat-input { background: #f0f2f5; padding: 10px 15px; display: flex; gap: 10px; align-items: center; }
        .media-chat { max-width: 100%; border-radius: 8px; margin-top: 5px; }
    </style>
</head>
<body>
    <div class="chat-header">
        <a href="/messages"><i class="fas fa-arrow-right fa-lg"></i></a>
        <div class="bg-light rounded-circle d-flex justify-content-center align-items-center" style="width: 40px; height: 40px; color: #064e3b; font-weight: bold;">{{ other_user[0] }}</div>
        <strong class="fs-5">{{ other_user }}</strong>
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
                </div>
            {% else %}
                <div class="msg-bubble msg-received">
                    {% if msg.content %}{{ msg.content }}{% endif %}
                    {% if msg.media %}
                        {% if msg.media_type == 'image' %}<img src="{{ url_for('static', filename='uploads/' + msg.media) }}" class="media-chat">
                        {% elif msg.media_type == 'video' %}<video controls class="media-chat"><source src="{{ url_for('static', filename='uploads/' + msg.media) }}"></video>{% endif %}
                    {% endif %}
                </div>
            {% endif %}
        {% endfor %}
    </div>
    <form action="/chat/{{ other_user }}" method="POST" enctype="multipart/form-data" class="chat-input">
        <label for="chat-media" class="btn btn-light text-success mb-0"><i class="fas fa-camera fa-lg"></i></label>
        <input type="file" name="media" id="chat-media" class="d-none" accept="image/*,video/*">
        <input type="text" name="content" class="form-control rounded-pill" placeholder="اكتب رسالة..." autocomplete="off" style="border-radius: 25px;">
        <button type="submit" class="btn btn-success rounded-circle" style="background:#064e3b; width: 45px; height: 45px;"><i class="fas fa-paper-plane"></i></button>
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
            new_post = Post(author=current_user.username, content=content, media=media_name, media_type=media_type)
            db.session.add(new_post)
            db.session.commit()
        
        return redirect(url_for('feed'))

    posts = Post.query.order_by(Post.timestamp.desc()).all()
    for post in posts:
        post.likes_count = PostLike.query.filter_by(post_id=post.id).count()
        post.comments = Comment.query.filter_by(post_id=post.id).all()
        post.is_liked = PostLike.query.filter_by(post_id=post.id, username=current_user.username).first() is not None
        author_user = User.query.filter_by(username=post.author).first()
        post.author_pic = author_user.profile_pic if author_user else 'default.png'
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
