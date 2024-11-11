from flask import Flask, render_template, redirect, url_for, request, session, g, flash
from flask_login import current_user, login_user, logout_user, LoginManager, login_required
from flask_bcrypt import Bcrypt

from model import db, insert_data, delete_one, Uzivatel, Rezervace

from usecase import hledani_zarizeni, ziskat_vsechny_typy, seznam_atelieru, sledovani_vypujcek

from datetime import timedelta
from functools import wraps # Dekorátor
import pymysql
pymysql.install_as_MySQLdb()

# Vytvoreni flask aplikace
app = Flask(__name__)

# Pripojeni k databazi lokalni MySQL/google cloud
#app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://sammy:password@localhost/demo'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://artist:&.{lE0A1i2&G$t3j@35.187.170.251/umelecka_skola'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'mujskrytyklicpaktozmenitnaneco'

db.init_app(app)

bcrypt = Bcrypt(app)
# Prihlasovaci logika pres flask tridu LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
@login_manager.user_loader

# Nastaveni funkce pro prihlasovani uzivatelu (vyhledani v databazi podle ID)
def load_user(user_id):
    return Uzivatel.query.get(user_id)

# Routes pro jednotlive stranky databaze
@app.route('/')
def index():
    return render_template('home.html')

@app.route('/database')
def database():
    return render_template('database.html')

# Vytvori databazi
@app.route('/db')
def create_db():    
    with app.app_context():
        db.create_all()
    flash('Databaze byla vytvorena', 'success')
    return render_template('database.html')

# Zruseni vsech tabulek v databazi
@app.route('/dropdb')
def drop_db():
    db.drop_all()
    flash('Databaze byla zrusena', 'success')
    return render_template('database.html')

# Naplneni databaze daty
@app.route('/insert')
def insert():
    insert_data(bcrypt)
    #delete_one()
    flash('Byly vlozeny zaznamy do db', 'success')
    return render_template('database.html')

# Regristace noveho uzivatele v systemu
@app.route('/register', methods=['GET', 'POST'])
def register():
    # Pokud je volana metoddou GET, zobrazi se registracni formular
    if request.method == 'GET':
        return render_template('auth/register.html')
    # Po stiknuti tlacitka se vola metoda POST, ktera zpracuje data z formulare
    elif request.method == 'POST':
        login = request.form.get('login')
        password = request.form.get('pwd')
        
        if Uzivatel.query.filter_by(login=login).first():
            flash('Uživatel s daným loginem již existuje', 'danger')
            return render_template('auth/register.html')
        
        hashed_password = bcrypt.generate_password_hash(password)   # Hashovani hesla kvuli bezpecnosti
        new_user = Uzivatel(login=login, heslo=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Úspěšně zaregistrovan, přihlas se', 'success')
        return redirect(url_for('index'))

# Prihlaseni uzivatele do systemu
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('auth/login.html')
    elif request.method == 'POST':
        login = request.form.get('login')
        password = request.form.get('pwd')
        
        user = Uzivatel.query.filter_by(login=login).first()    # Vyhledavani uzivatele v databazi podle loginu
        if user is None:
            flash('Uzivatel s danym loginem neexsituje', 'danger')
            return render_template('auth/login.html')
        if bcrypt.check_password_hash(user.heslo, password):    # V databazi nalezneme heslo u uzivatele a zkontrolujeme shodu
            login_user(user)
            flash('Úspěšně přihlášen', 'success')
            return redirect(url_for('index'))
        else:
            flash('Chybný login nebo heslo', 'danger')
    return render_template('auth/login.html')

# Odhlaseni uzivatele ze systemu
@app.route('/logout')
@login_required         # Aby bylo mozne se odhlasit, musi byt uzivatel prihlasen
def logout():
    logout_user()
    flash('Byl jste odhlášen', 'success')
    return redirect(url_for('home'))

@app.route('/profile')
@login_required
def profile():
    rezervace = Rezervace.query.filter_by(id_uzivatel=current_user.id).all()
    return render_template('profile.html', rezervace=rezervace)

@app.route('/user_change', methods=['GET', 'POST'])
@login_required
def user_change():
    if request.method == 'GET':
        return render_template('auth/user_change.html')
    elif request.method == 'POST':
        new_login = request.form.get('new_login')
        new_password = request.form.get('new_pwd')
        new_password_check = request.form.get('new_pwd2')
        
        if not new_login and not new_password:
            flash('Nebyly zadány žádné nové údaje', 'danger')
            return render_template('auth/user_change.html')
            
        elif new_password:
            hashed_password = bcrypt.generate_password_hash(new_password)
            if new_password == new_password_check:
                current_user.heslo = hashed_password
            else:
                flash('Hesla se neshodují', 'danger')
                return render_template('auth/user_change.html')
                
        if new_login:
            if Uzivatel.query.filter_by(login=new_login).first():
                flash('Uživatel s daným loginem již existuje', 'danger')
                return render_template('auth/user_change.html')
            current_user.login = new_login
        
        db.session.commit()
        flash('Úspěšně změněno', 'success')
        return redirect(url_for('profile'))
        

# Nastaveni timeoutu, po 30minutach neaktivity bude uzivatel odhlasen
@app.before_request
def before_request():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=30)
    session.modified = True
    g.user = current_user

# role_required - dekorátor, ověřuje roli uživatele
def role_required(roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            for r in roles:
                if current_user.role == r:
                    return f(*args, **kwargs)
            flash('Nemáte přístupová práva na tuto stránku', 'danger')
            return redirect(url_for('home'))
        return decorated_function
    return decorator

@app.route('/admin')
@login_required
@role_required(['admin'])
def protected():
    return 'Stránka pouze pro admina'

@app.route('/stranka')
@login_required
@role_required(['admin', 'vyucujici', 'uzivatel'])
def test_roles():
    return 'Stranka je pro vsechny krome spravce (nemame ho radi :)))'


@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/search_devices', methods=['GET'])
@login_required
def search_devices():
    nazev = request.args.get('nazev')
    id_typ = request.args.get('id_typ')
    id_atelier = request.args.get('id_atelier')
    
    devices = hledani_zarizeni(nazev=nazev, id_typ=id_typ, id_atelier=id_atelier)
    typy = ziskat_vsechny_typy()
    ateliery = seznam_atelieru()
    
    return render_template('user/search_devices.html', devices=devices, typy=typy, ateliery=ateliery)

@app.route('/my_devices')
@login_required
def my_devices():
    borrow = sledovani_vypujcek(current_user.id)
    return render_template('user/my_devices.html', borrow=borrow)

if __name__ == '__main__':
    app.run(debug=True)