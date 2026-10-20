from flask import Flask, render_template_string, jsonify
import os

app = Flask(__name__)

# ==========================================
# بيانات تجريبية (سنستبدلها بقاعدة بيانات لاحقاً)
# ==========================================
PLAYERS = [
    {"id": 1, "name": "أحمد علي", "position": "مهاجم", "number": 9, "image": "https://i.pravatar.cc/150?img=11"},
    {"id": 2, "name": "محمد حسن", "position": "وسط", "number": 8, "image": "https://i.pravatar.cc/150?img=12"},
    {"id": 3, "name": "خالد سعيد", "position": "مدافع", "number": 4, "image": "https://i.pravatar.cc/150?img=13"},
    {"id": 4, "name": "عمر يوسف", "position": "حارس", "number": 1, "image": "https://i.pravatar.cc/150?img=14"},
]

MATCHES = [
    {"home": "نسور حجرودسالم", "away": "فريق الوحدة", "date": "2026-11-01", "time": "17:00", "status": "قادمة", "score": ""},
    {"home": "نسور حجرودسالم", "away": "فريق الأمل", "date": "2026-10-20", "time": "16:30", "status": "منتهية", "score": "3 - 1"},
]

# ==========================================
# قوالب HTML (التصميم العصري)
# ==========================================
BASE_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>نادي نسور حجرودسالم</title>
    <!-- Bootstrap 5 CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <!-- Google Fonts -->
    <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary-color: #1e5631; /* أخضر غامق */
            --secondary-color: #d4af37; /* ذهبي */
            --bg-light: #f8f9fa;
        }
        body {
            font-family: 'Tajawal', sans-serif;
            background-color: var(--bg-light);
            color: #333;
        }
        /* شريط التنقل */
        .navbar {
            background-color: var(--primary-color);
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .navbar-brand {
            color: var(--secondary-color) !important;
            font-weight: 900;
            font-size: 1.5rem;
        }
        .nav-link {
            color: #fff !important;
            font-weight: 700;
            transition: color 0.3s;
        }
        .nav-link:hover {
            color: var(--secondary-color) !important;
        }
        /* قسم الهيرو */
        .hero-section {
            background: linear-gradient(rgba(30, 86, 49, 0.8), rgba(30, 86, 49, 0.8)), url('https://images.unsplash.com/photo-1508098682722-e99c43a406b2?q=80&w=2070&auto=format&fit=crop') no-repeat center center/cover;
            color: white;
            padding: 100px 0;
            text-align: center;
            border-bottom: 5px solid var(--secondary-color);
        }
        .hero-title {
            font-size: 3.5rem;
            font-weight: 900;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        }
        .hero-subtitle {
            font-size: 1.5rem;
            font-weight: 400;
            color: var(--secondary-color);
        }
        /* تنسيق الكروت */
        .card-custom {
            border: none;
            border-radius: 15px;
            box-shadow: 0 10px 20px rgba(0,0,0,0.05);
            transition: transform 0.3s, box-shadow 0.3s;
            overflow: hidden;
        }
        .card-custom:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 30px rgba(0,0,0,0.1);
        }
        .card-header-custom {
            background-color: var(--primary-color);
            color: var(--secondary-color);
            font-weight: 700;
            text-align: center;
            border-bottom: 3px solid var(--secondary-color);
        }
        /* صفحة اللاعبين */
        .player-card {
            text-align: center;
            padding: 20px;
        }
        .player-img {
            width: 120px;
            height: 120px;
            border-radius: 50%;
            object-fit: cover;
            border: 4px solid var(--secondary-color);
            margin-bottom: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
        .player-name {
            font-weight: 900;
            color: var(--primary-color);
            font-size: 1.2rem;
        }
        .player-position {
            color: #777;
            font-weight: 700;
        }
        .player-number {
            background-color: var(--secondary-color);
            color: var(--primary-color);
            font-weight: 900;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            margin-top: 10px;
            font-size: 1.2rem;
        }
        /* صفحة المباريات */
        .match-card {
            padding: 20px;
            text-align: center;
        }
        .match-teams {
            font-size: 1.3rem;
            font-weight: 700;
        }
        .match-vs {
            font-size: 2rem;
            font-weight: 900;
            color: var(--secondary-color);
        }
        .match-score {
            font-size: 1.8rem;
            font-weight: 900;
            color: var(--primary-color);
            background-color: #e9ecef;
            padding: 5px 15px;
            border-radius: 10px;
            display: inline-block;
        }
        .badge-upcoming {
            background-color: #17a2b8;
            color: white;
            padding: 5px 10px;
            border-radius: 5px;
            font-weight: 700;
        }
        .badge-finished {
            background-color: var(--primary-color);
            color: white;
            padding: 5px 10px;
            border-radius: 5px;
            font-weight: 700;
        }
        /* تذييل الصفحة */
        footer {
            background-color: var(--primary-color);
            color: white;
            text-align: center;
            padding: 20px 0;
            margin-top: 50px;
            border-top: 4px solid var(--secondary-color);
        }
    </style>
</head>
<body>

    <!-- شريط التنقل -->
    <nav class="navbar navbar-expand-lg navbar-dark">
        <div class="container">
            <a class="navbar-brand" href="/">🦅 نسور حجرودسالم</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item"><a class="nav-link" href="/">الرئيسية</a></li>
                    <li class="nav-item"><a class="nav-link" href="/players">اللاعبون</a></li>
                    <li class="nav-item"><a class="nav-link" href="/matches">المباريات</a></li>
                </ul>
            </div>
        </div>
    </nav>

    <!-- محتوى الصفحة -->
    {% block content %}{% endblock %}

    <!-- تذييل الصفحة -->
    <footer>
        <div class="container">
            <p class="mb-0">جميع الحقوق محفوظة &copy; 2026 - نادي نسور حجرودسالم</p>
            <p class="mb-0" style="font-size: 0.9rem;">صنع بحب بواسطة أبناء حجرودسالم</p>
        </div>
    </footer>

    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

INDEX_HTML = BASE_HTML.replace('{% block content %}{% endblock %}', """
<!-- قسم الهيرو -->
<section class="hero-section">
    <div class="container">
        <h1 class="hero-title">مرحباً بكم في نادي نسور حجرودسالم</h1>
        <p class="hero-subtitle">حيث تلتقي الروح الرياضية بالطموح</p>
    </div>
</section>

<!-- قسم الترحيب -->
<div class="container mt-5">
    <div class="row">
        <div class="col-md-8 mx-auto text-center">
            <h2 class="mb-4" style="color: var(--primary-color); font-weight: 900;">عن النادي</h2>
            <p class="lead" style="line-height: 1.8;">
                نادي نسور حجرودسالم هو أكثر من مجرد فريق كرة قدم، هو عائلة واحدة تجمعها المحبة والطموح. 
                نسعى دائماً لتحقيق البطولات، ونؤمن بأن الروح الرياضية هي أساس النجاح.
            </p>
        </div>
    </div>
</div>
""")

PLAYERS_HTML = BASE_HTML.replace('{% block content %}{% endblock %}', """
<div class="container mt-5">
    <h2 class="text-center mb-5" style="color: var(--primary-color); font-weight: 900;">⭐ نجوم الفريق ⭐</h2>
    <div class="row g-4">
        {% for player in players %}
        <div class="col-md-3 col-sm-6">
            <div class="card card-custom player-card">
                <img src="{{ player.image }}" class="player-img mx-auto" alt="{{ player.name }}">
                <h4 class="player-name">{{ player.name }}</h4>
                <p class="player-position">{{ player.position }}</p>
                <div class="player-number">{{ player.number }}</div>
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
        {% for match in matches %}
        <div class="col-md-6">
            <div class="card card-custom match-card">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <span class="badge {{ 'badge-upcoming' if match.status == 'قادمة' else 'badge-finished' }}">{{ match.status }}</span>
                    <span style="font-weight: 700; color: #777;">{{ match.date }} | {{ match.time }}</span>
                </div>
                <div class="d-flex justify-content-center align-items-center gap-3">
                    <span class="match-teams">{{ match.home }}</span>
                    {% if match.status == 'منتهية' %}
                        <span class="match-score">{{ match.score }}</span>
                    {% else %}
                        <span class="match-vs">VS</span>
                    {% endif %}
                    <span class="match-teams">{{ match.away }}</span>
                </div>
            </div>
        </div>
        {% endfor %}
    </div>
</div>
""")

# ==========================================
# المسارات (Routes)
# ==========================================
@app.route('/')
def home():
    return render_template_string(INDEX_HTML)

@app.route('/players')
def players():
    return render_template_string(PLAYERS_HTML, players=PLAYERS)

@app.route('/matches')
def matches():
    return render_template_string(MATCHES_HTML, matches=MATCHES)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
