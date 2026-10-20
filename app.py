from flask import Flask, render_template_string, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-secret-key-for-club'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///club.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# ==========================================
# نماذج قاعدة البيانات (الجداول)
# ==========================================
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(100), nullable=False)
    receiver = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# إنشاء الجداول إذا لم تكن موجودة
with app.app_context():
    db.create_all()
    # إضافة مستخدم مدير افتراضي إذا لم يوجد أي مستخدم
    if not User.query.first():
        admin = User(username='admin', password_hash=generate_password_hash('admin123'))
        db.session.add(admin)
        db.session.commit()

# ==========================================
# القوالب (HTML) - تصميم موحد
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
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark">
        <div class="container">
            <a class="navbar-brand" href="/">🦅 نسور حجرودسالم</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav"><span class="navbar-toggler-icon"></span></button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item"><a class="nav-link" href="/">الرئيسية</a></li>
                    <li class="nav-item"><a class="nav-link" href="/players">اللاعبون</a></li>
                    <li class="nav-item"><a class="nav-link" href="/matches">المباريات</a></li>
                    {% if current_user.is_authenticated %}
                        <li class="nav-item"><a class="nav-link text-warning" href="/messages">الرسائل</a></li>
                        <li class="nav-item"><a class="nav-link text-danger" href="/logout">تسجيل خروج ({{ current_user.username }})</a></li>
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

INDEX_HTML = BASE_HTML.replace('{% block content %}{% endblock %}', """
<section class="hero-section">
    <div class="container">
        <h1 class="hero-title">مرحباً بكم في نادي نسور حجرودسالم</h1>
        <p class="lead">حيث تلتقي الروح الرياضية بالطموح</p>
    </div>
</section>
<div class="container mt-5 text-center">
    <h2 style="color: var(--primary-color); font-weight: 900;">أهلاً بك يا {{ current_user.username if current_user.is_authenticated else 'زائر' }}</h2>
    <p>هذا هو الموقع الرسمي للنادي. سجل دخولك للتواصل مع الأعضاء.</p>
</div>
""")

LOGIN_HTML = BASE_HTML.replace('{% block content %}{% endblock %}', """
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

REGISTER_HTML = BASE_HTML.replace('{% block content %}{% endblock %}', """
<div class="auth-form">
    <h3 class="text-center mb-4" style="color: var(--primary-color);">إنشاء حساب جديد</h3>
    <form method="POST">
        <div class="mb-3"><label class="form-label">اسم المستخدم</label><input type="text" name="username" class="form-control" required></div>
        <div class="mb-3"><label class="form-label">كلمة المرور</label><input type="password" name="password" class="form-control" required></div>
        <button type="submit" class="btn btn-gold w-100">تسجيل</button>
    </form>
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

# بيانات تجريبية للاعبين (كما هي)
PLAYERS = [
    {"name": "أحمد علي", "position": "مهاجم", "number": 9, "image": "https://i.pravatar.cc/150?img=11"},
    {"name": "محمد حسن", "position": "وسط", "number": 8, "image": "https://i.pravatar.cc/150?img=12"},
]
PLAYERS_HTML = BASE_HTML.replace('{% block content %}{% endblock %}', """
<div class="container mt-5">
    <h2 class="text-center mb-4" style="color: var(--primary-color);">⭐ نجوم الفريق ⭐</h2>
    <div class="row g-4">
        {% for player in players %}
        <div class="col-md-3 col-sm-6">
            <div class="card card-custom text-center p-3">
                <img src="{{ player.image }}" class="rounded-circle mx-auto mb-3" style="width: 120px; height: 120px; object-fit: cover; border: 3px solid var(--secondary-color);">
                <h4 style="color: var(--primary-color);">{{ player.name }}</h4>
                <p class="text-muted">{{ player.position }}</p>
                <span class="badge bg-warning text-dark fs-6">{{ player.number }}</span>
            </div>
        </div>
        {% endfor %}
    </div>
</div>
""")

# ==========================================
# المسارات
# ==========================================
@app.route('/')
def home(): return render_template_string(INDEX_HTML)

@app.route('/players')
def players(): return render_template_string(PLAYERS_HTML, players=PLAYERS)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password_hash, request.form['password']):
            login_user(user)
            flash('تم تسجيل الدخول بنجاح!', 'success')
            return redirect(url_for('home'))
        flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'danger')
    return render_template_string(LOGIN_HTML)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if User.query.filter_by(username=request.form['username']).first():
            flash('اسم المستخدم موجود بالفعل', 'danger')
            return redirect(url_for('register'))
        new_user = User(username=request.form['username'], password_hash=generate_password_hash(request.form['password']))
        db.session.add(new_user)
        db.session.commit()
        flash('تم إنشاء الحساب بنجاح! يمكنك تسجيل الدخول الآن.', 'success')
        return redirect(url_for('login'))
    return render_template_string(REGISTER_HTML)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('تم تسجيل الخروج.', 'info')
    return redirect(url_for('home'))

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
