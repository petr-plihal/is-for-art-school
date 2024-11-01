from flask import Flask, render_template, redirect
import pymysql
from model import db, insert_data, delete_one

import usecase
from model import Uzivatel

# request, url_for, session - pro přihlášení
# flash - pro zobrazení zpráv uživateli
from flask import request, flash, url_for, session

# Dekorátor
from functools import wraps


pymysql.install_as_MySQLdb()

# Vytvoreni flask aplikace
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Nastavte tajný klíč pro podepisování cookies (ze strany serveru)

# Pripojeni k databazi lokalni MySQL/google cloud
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://sammy:password@localhost/demo'
#app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://artist:&.{lE0A1i2&G$t3j@35.187.170.251/umelecka_skola'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Routes pro jednotlive stranky databaze
# Nacte pocatecni stranku
@app.route('/')
def index():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = usecase.over_login(username, password)
        if user:
            session['user_id'] = user.id
            session['role'] = user.role
            flash('Úspěšně přihlášen', 'success')
            return redirect(url_for('index'))
        else:
            flash('Chybný login nebo heslo', 'danger')
    return render_template('auth/login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Byl jste odhlášen', 'success')
    return redirect(url_for('home'))

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# role_required - dekorátor, ověřuje roli uživatele
def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'role' not in session or session['role'] != role:
                flash('Nemáte přístupová práva na tuto stránku', 'danger')
                return redirect(url_for('home'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/admin')
@login_required
@role_required('admin')
def protected():
    return 'Stránka pouze pro admina'

@app.route('/home')
def home():
    return render_template('home.html')

if __name__ == '__main__':
    app.run(debug=True)