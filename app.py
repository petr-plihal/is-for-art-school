from flask import Flask, render_template, redirect, url_for, request, session, g, flash
from flask_login import current_user, login_user, logout_user, LoginManager, login_required
from flask_bcrypt import Bcrypt
from model import db, insert_data, delete_one, Uzivatel, Rezervace, Zarizeni
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

@app.route('/vypujcky')
def vypujcky():
    vypujcky = Rezervace.query.filter_by(id_vyucujici=current_user.id_vyucujici).all()
    all_users = get_all_users()
    all_devices = get_all_device()
    users_devices = get_users_devices()
    return render_template('vypujcky.html', vypujcky=vypujcky, all_users=all_users, all_devices=all_devices, users_devices=users_devices)

def get_users_devices():
    devices = Zarizeni.query.filter_by(id_vyucujici=current_user.id_vyucujici).all()
    return devices

def get_all_device():
    devices = Zarizeni.query.all()
    all_devices = {}

    for device in devices:
        all_devices[device.id] = device.nazev

    return all_devices

def get_all_users():
    users = Uzivatel.query.all()
    all_users = {}

    for user in users:
        all_users[user.id] = user.login
    
    return all_users

@app.route('/update_rezervace', methods=['POST'])
def update_rezervace():
    reservation_id = request.form.get('reservation_id')

    new_status = request.form.get('status')
    new_device = request.form.get('device')
    new_user = request.form.get('user')
    new_start_date = request.form.get('start_date')
    new_end_date = request.form.get('end_date')
    
    # Aktualizace rezervace
    reservation = Rezervace.query.get(reservation_id)
    
    if new_status != "_NONE_":
        reservation.stav = new_status

    if new_device != "_NONE_":
        reservation.zarizeni = Zarizeni.query.get(new_device)

    if new_user:
        new_user_id = Uzivatel.query.filter_by(login=new_user).first()
        print(f"tady")
        if new_user_id is not None:
            reservation.id_uzivatel = new_user_id.id

    if new_start_date:
        reservation.datum_od = new_start_date

    if new_end_date:
        reservation.datum_do = new_end_date
    
    db.session.commit()
    
    return redirect(url_for('vypujcky'))


if __name__ == '__main__':
    app.run(debug=True)