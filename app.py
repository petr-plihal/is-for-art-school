from flask import Flask, render_template, redirect, url_for, request, session, g, flash
from flask_login import current_user, login_user, logout_user, LoginManager, login_required
from flask_bcrypt import Bcrypt
from sqlalchemy import or_
from datetime import timedelta, date, datetime
from functools import wraps # Dekorátor
import pymysql
pymysql.install_as_MySQLdb()

from model import *
from vyucujici import *
from admin import *

# Vytvoreni flask aplikace
app = Flask(__name__)

# Pripojeni k databazi lokalni MySQL/google cloud
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://sammy:password@localhost/demo'
#app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://artist:&.{lE0A1i2&G$t3j@35.187.170.251/umelecka_skola'
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

#           ----------------- Vyučující -----------------
# Stránka pro zobrazní všech zařízení daného vyučujícího
@app.route('/zarizeni_sprava')
@login_required
@role_required(['vyucujici', 'admin'])
def zarizeni_sprava():
    if current_user.role == 'admin':
        zarizeni = Zarizeni.query.all()
    else:
        vyucujici = Vyucujici.query.filter_by(id=current_user.id).first_or_404()
        zarizeni = Zarizeni.query.filter_by(id_vyucujici=vyucujici.id_vyucujici).all()
    return render_template('vyucujici/zarizeni_sprava.html', zarizeni=zarizeni)

# Stránka pro správu jednotlivých zařízení
@app.route('/zarizeni_sprava/<int:id_zarizeni>', methods=['GET', 'POST'])
@login_required
@role_required(['vyucujici', 'admin'])
def zarizeni_by_id(id_zarizeni):
    zarizeni = Zarizeni.query.filter_by(id=id_zarizeni).first_or_404()
    typ = Typ.query.all()
    navraceni = Navraceni.query.filter_by(id_zarizeni=id_zarizeni).all()
    
    if not kontrola_pristupu_vyucujici(current_user.id, id_zarizeni):
        flash('Nemáte přístupová práva na tuto stránku', 'danger')
        return redirect(url_for('home'))
    
    if request.method == 'GET':
        return render_template('vyucujici/zarizeni_by_id.html', zarizeni=zarizeni, typ=typ, navraceni=navraceni)
    # Zpracování formuláře pro změnu udajů o zařízení (vše jsou řetězce)
    elif request.method == 'POST' and 'data_change' in request.form:
        nazev = request.form.get('name')
        typ_id = request.form.get('typ')
        rok_vyroby = request.form.get('rok_vyroby')
        datum_nakupu = request.form.get('datum_nakupu')
        doba_vypujcky = request.form.get('doba_vypujcky')
        
        datum_nakupu = datum_nakupu.split('-') # Rozdeleni data na rok, mesic, den
        datum_nakupu = date(int(datum_nakupu[0]), int(datum_nakupu[1]), int(datum_nakupu[2]))
        
        # Kontrola validity dat z formuláře
        if int(rok_vyroby) > int(datum_nakupu.year):
            flash('Rok výroby nemůže být větší než datum nákupu', 'danger')
            return redirect(url_for('zarizeni_by_id', id_zarizeni=id_zarizeni))
        
        if int(rok_vyroby) > int(datetime.today().year) or datum_nakupu > datetime.today().date():
            flash('Nelze zadat budoucí datum', 'danger')
            return redirect(url_for('zarizeni_by_id', id_zarizeni=id_zarizeni))
        
        if int(doba_vypujcky) < 1:
            flash('Doba výpůjčky musí být větší než 0', 'danger')
            return redirect(url_for('zarizeni_by_id', id_zarizeni=id_zarizeni))
        
        # Aktualizace dat v databázi k zařízení
        aktualizace_zarizeni(id_zarizeni, nazev, int(typ_id), datetime(int(rok_vyroby), 1, 1), datum_nakupu, int(doba_vypujcky))
        flash('Změny byly uloženy', 'success')
        return redirect(url_for('zarizeni_by_id', id_zarizeni=id_zarizeni))
    
    # Zpracování formuláře pro přidání nových datumů vypůjčení/vrácení
    elif request.method == 'POST' and 'date_add' in request.form:
        datum_vraceni = request.form.get('datum_vraceni')
        typ = request.form.get('vraceni')
        datum_vraceni = format_datum(datum_vraceni)       

        # Kotrola validity dat
        if datum_vraceni < datetime.today():
            flash('Nelze zadat minulé datum', 'danger')
            return redirect(url_for('zarizeni_by_id', id_zarizeni=id_zarizeni))
        
        # Kontrola duplicity záznamu
        if Navraceni.query.filter_by(id_zarizeni=id_zarizeni).filter_by(vraceni=typ).filter_by(datum=datum_vraceni).first():
            flash('Záznam již existuje', 'danger')
            return redirect(url_for('zarizeni_by_id', id_zarizeni=id_zarizeni))
        
        # Přidaní nového záznamu o datu navrácení/vypůjčení
        pridani_vraceni(id_zarizeni, typ, datum_vraceni)
        flash('Změny byly uloženy', 'success')
        return redirect(url_for('zarizeni_by_id', id_zarizeni=id_zarizeni))
    
    else:
        flash('Chyba', 'danger')
        return redirect(url_for('zarizeni_by_id', id_zarizeni=id_zarizeni))

# Stránka pro smazání datumu pro vypůjčení/vrácení
@app.route('/zarizeni_sprava/<int:id_zarizeni>/delete/<int:id_navraceni>')
@login_required
@role_required(['vyucujici', 'admin'])
def delete_navraceni(id_zarizeni, id_navraceni):
    if not kontrola_pristupu_vyucujici(current_user.id, id_zarizeni):
        flash('Nemáte přístupová práva na tuto stránku', 'danger')
        return redirect(url_for('home'))
    
    date_to_delete = Navraceni.query.filter_by(id=id_navraceni).first_or_404()
    count = Navraceni.query.filter_by(id_zarizeni=id_zarizeni).filter_by(vraceni=date_to_delete.vraceni).count()
    # Kontrola jestli to není poslední záznam - alespoň jeden musí zůstat
    if count == 1:
        flash('Nelze smazat poslední záznam', 'danger')
        return redirect(url_for('zarizeni_by_id', id_zarizeni=id_zarizeni))
    
    # Smazání záznamu
    db.session.delete(date_to_delete)
    db.session.commit()
    flash('Záznam byl smazán', 'success')
    return redirect(url_for('zarizeni_by_id', id_zarizeni=id_zarizeni))

# Stránka pro přidání nového zařízení
@app.route('/zarizeni_sprava/zarizeni_pridat', methods=['GET', 'POST'])
@login_required
@role_required(['vyucujici', 'admin'])
def zarizeni_pridat():
    typ = Typ.query.all()
    if current_user.role == 'admin':
        ateliery = Atelier.query.all()
    else:
        vyucujici = Vyucujici.query.filter_by(id=current_user.id).first_or_404()
        # Získání všech ateliérů, které vyučující vyučuje, pomocí propojení tabulky Ateliér a atelier_vyucujici
        ateliery = db.session.query(Atelier).join(atelier_vyucujici, atelier_vyucujici.c.id_atelier == Atelier.id).filter(atelier_vyucujici.c.id_vyucujici == vyucujici.id_vyucujici).all()
        
    if request.method == 'GET':
        return render_template('vyucujici/zarizeni_pridat.html', typ=typ, atelier=ateliery)
    # Přidání nového zařízení skrze formulář
    elif request.method == 'POST':
        nazev = request.form.get('name')
        typ_id = request.form.get('typ')
        atelier_id = request.form.get('atelier')
        rok_vyroby = request.form.get('rok_vyroby')
        datum_nakupu = request.form.get('datum_nakupu')
        doba_vypujcky = request.form.get('doba_vypujcky')
        
        datum_nakupu = datum_nakupu.split('-') # Rozdeleni data na rok, mesic, den
        datum_nakupu = date(int(datum_nakupu[0]), int(datum_nakupu[1]), int(datum_nakupu[2]))
        
        # Kontrola validity dat od uživatele
        if int(rok_vyroby) > int(datum_nakupu.year):
            flash('Rok výroby nemůže být větší než datum nákupu', 'danger')
            return redirect(url_for('zarizeni_pridat'))
        
        if int(rok_vyroby) > int(datetime.today().year) or datum_nakupu > datetime.today().date():
            flash('Nelze zadat budoucí datum', 'danger')
            return redirect(url_for('zarizeni_pridat'))
        
        if int(doba_vypujcky) < 1:
            flash('Doba výpůjčky musí být větší než 0', 'danger')
            return redirect(url_for('zarizeni_pridat'))
        
        # Přidání nového data navrácení pro přidávané zařízení
        datum_navraceni = request.form.get('datum_navraceni')
        datum_vypujceni = request.form.get('datum_vypujceni')
        datum_navraceni = format_datum(datum_navraceni)
        datum_vypujceni = format_datum(datum_vypujceni)                
        
        if datum_navraceni < datetime.today() or datum_vypujceni < datetime.today():
            flash('Nelze zadat minulé datum', 'danger')
            return redirect(url_for('zarizeni_pridat'))
        
        # Přidání nového zařízení do databáze
        nove_zarizeni_id = pridat_zarizeni(nazev, int(typ_id), datetime(int(rok_vyroby), 1, 1), datum_nakupu, int(doba_vypujcky), int(atelier_id), vyucujici.id_vyucujici)
        
        # Propojení zařízení s daty navrácení z tabulky Navrácení
        pridani_vraceni(nove_zarizeni_id, "Vypujceni", datum_vypujceni)
        pridani_vraceni(nove_zarizeni_id, "Navraceni", datum_navraceni)
        
        flash('Změny byly uloženy', 'success')
        return redirect(url_for('zarizeni_sprava'))
    
    else:
        flash('Chyba', 'danger')
        return redirect(url_for('zarizeni_pridat'))

# Smazání zařízení
@app.route('/zarizeni_sprava/<int:id_zarizeni>/delete_zarizeni')
@login_required
@role_required(['vyucujici', 'admin'])
def zarizeni_smazat(id_zarizeni):
    if not kontrola_pristupu_vyucujici(current_user.id, id_zarizeni):
        flash('Nemáte přístupová práva na tuto stránku', 'danger')
        return redirect(url_for('home'))
    
    # Pokud je zařízení právě vypůjčené nebo rezervované nelze jej smazat
    if Rezervace.query.filter_by(id_zarizeni=id_zarizeni).filter(or_(Rezervace.stav=='Rezervovano', Rezervace.stav=='Vypujceno')).first():
        flash('Nelze smazat zařízení, které je rezervované nebo vypůjčené', 'danger')
        return redirect(url_for('zarizeni_sprava'))
    
    odstraneni_navraceni(id_zarizeni)
    odstraneni_zarizeni(id_zarizeni)
    flash('Záznam byl smazán', 'success')
    return redirect(url_for('zarizeni_sprava'))

# Zakázání/povolení vypůjčení zařízení
@app.route('/zarizeni_sprava/<int:id_zarizeni>/zarizeni_zakazat')
@login_required
@role_required(['vyucujici', 'admin'])
def zarizeni_zakazat(id_zarizeni):
    zarizeni_zakazat = Zarizeni.query.filter_by(id=id_zarizeni).first_or_404()    
    if not kontrola_pristupu_vyucujici(current_user.id, zarizeni_zakazat.id):
        flash('Nemáte přístupová práva na tuto stránku', 'danger')
        return redirect(url_for('home'))
    
    # Pokud je zařízení již rezervováno k vypůjčení nelze jej zakázat
    if Rezervace.query.filter_by(id_zarizeni=id_zarizeni).filter(Rezervace.stav=='Rezervovano').first():
        flash('Nelze zakazat půjčení zařízení, které je rezervované', 'danger')
        return redirect(url_for('zarizeni_sprava'))
    
    zarizeni_zakazat.povolene = not zarizeni_zakazat.povolene
    db.session.commit()
    
    flash('Zařízení bylo změněno', 'success')
    return redirect(url_for('zarizeni_sprava'))

# Omezení vypůjčení zařízení na konkrétní uživatele
@app.route('/zarizeni_sprava/<int:id_zarizeni>/zarizeni_uzivatele_upravit')
@login_required
@role_required(['vyucujici', 'admin'])
def zarizeni_uzivatele_upravit(id_zarizeni):
    if not kontrola_pristupu_vyucujici(current_user.id, id_zarizeni):
        flash('Nemáte přístupová práva na tuto stránku', 'danger')
        return redirect(url_for('home'))
    
    zarizeni = Zarizeni.query.filter_by(id=id_zarizeni).first_or_404()
    
    # Získání všech uživatelů, kteří patří do ateliéru, pomocí propojení tabulky Uživatel a atelier_uzivatel
    uzivatele_atelier = db.session.query(Uzivatel).join(atelier_uzivatel, atelier_uzivatel.c.id_uzivatel == Uzivatel.id).filter(atelier_uzivatel.c.id_atelier == zarizeni.id_atelier).all()
    # Získání všech uživatelů, na které je vypůjčení omezeno
    uzivatel_zaznamy = db.session.query(Uzivatel).join(zarizeni_uzivatel, zarizeni_uzivatel.c.id_uzivatel == Uzivatel.id).filter(zarizeni_uzivatel.c.id_zarizeni == id_zarizeni).all()
    # Oddelani uzivatelu, kteri jsou v tabulce zarizeni_uzivatel
    uzivatele_atelier = [uzivatel for uzivatel in uzivatele_atelier if uzivatel not in uzivatel_zaznamy]
    
    return render_template('vyucujici/zarizeni_uzivatele_upravit.html', zarizeni=zarizeni, uzivatele_atelier=uzivatele_atelier, uzivatel_zaznamy=uzivatel_zaznamy)

# Přidání uživatele do omezení
@app.route('/zarizeni_sprava/<int:id_zarizeni>/zarizeni_uzivatele_upravit/pridat/<int:id_uzivatele>')
@login_required
@role_required(['vyucujici', 'admin'])
def zarizeni_uzivatel_pridat(id_zarizeni, id_uzivatele):

    if not kontrola_pristupu_vyucujici(current_user.id, id_zarizeni):
        flash('Nemáte přístupová práva na tuto stránku', 'danger')
        return redirect(url_for('home'))
    
    pridat_zaznam_zarizeni_uzivatel(id_zarizeni, id_uzivatele)

    return redirect(url_for('zarizeni_uzivatele_upravit', id_zarizeni=id_zarizeni))

# Odebrání uživatele z omezení
@app.route('/zarizeni_sprava/<int:id_zarizeni>/zarizeni_uzivatele_upravit/odebrat/<int:id_uzivatele>')
@login_required
@role_required(['vyucujici', 'admin'])
def zarizeni_uzivatel_odebrat(id_zarizeni, id_uzivatele):

    if not kontrola_pristupu_vyucujici(current_user.id, id_zarizeni):
        flash('Nemáte přístupová práva na tuto stránku', 'danger')
        return redirect(url_for('home'))
    
    odebrat_zaznam_zarizeni_uzivatel(id_zarizeni, id_uzivatele)
    
    return redirect(url_for('zarizeni_uzivatele_upravit', id_zarizeni=id_zarizeni))

#           ----------------- Admin -----------------
# Admin stránka pro zobrazení ateliérů a uživatelů a správu ateliérů
@app.route('/admin', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def admin():
    if request.method == 'GET':
        ateliery = Atelier.query.all()
        uzivatele = Uzivatel.query.all()
        return render_template('admin/admin.html', ateliery=ateliery, uzivatele=uzivatele)
    
    # Přidání nového ateliéru
    elif request.method == 'POST' and "atelier_pridat" in request.form:
        nazev = request.form.get('atelier_name')
        if Atelier.query.filter_by(nazev=nazev).first():
            flash('Ateliér s daným názvem již existuje', 'danger')
            return redirect(url_for('admin'))
        else:
            atelier_pridat(nazev)
            flash('Ateliér byl přidán', 'success')
        return redirect(url_for('admin'))

# Smazání ateliéru
@app.route('/admin/atelier/<int:id_atelier>/delete', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def atelier_smazat(id_atelier):
    atelier = Atelier.query.get(id_atelier)
    if atelier:
        db.session.delete(atelier)
        db.session.commit()
        flash('Atelier byl smazán', 'success')
    return redirect(url_for('admin'))

# Změna názvu ateliéru
@app.route('/admin/atelier/<int:id_atelier>/zmena', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def atelier_zmena(id_atelier):
    if request.method == 'POST' and 'atelier_nazev' in request.form:
        novy_nazev = request.form.get('atelier_name')
        if Atelier.query.filter_by(nazev=novy_nazev).first():
            flash('Ateliér s daným názvem již existuje', 'danger')
            return redirect(url_for('admin'))
        else:
            atelier_zmena = Atelier.query.filter_by(id=id_atelier).first_or_404()
            atelier_zmena.nazev = novy_nazev
            db.session.commit()
            flash('Název atelieru byl úspěšně změněn', 'success')
        return redirect(url_for('admin'))

# Přidání nového správce k ateliéru
@app.route('/admin/spravce_sprava', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def spravce_sprava():
    if request.method == 'GET':
        uzivatele = Uzivatel.query.all()
        ateliery = Atelier.query.all()
        return render_template('admin/spravce_sprava.html', uzivatele=uzivatele, ateliery=ateliery)
    
    elif request.method == 'POST':
        id_uzivatel = int(request.form.get('uzivatel_id'))
        id_atelieru = int(request.form.get('atelier_id'))
        uzivatel = Uzivatel.query.filter_by(id=id_uzivatel).first()
        # Pokud je uživatel již správcem, kontrola jestli již nespravuje daný atelér
        if uzivatel.role == "spravce":
            if db.session.query(Spravce).join(atelier_spravce, atelier_spravce.c.id_spravce == Spravce.id_spravce).filter(atelier_spravce.c.id_atelier == id_atelieru).filter(Spravce.id == id_uzivatel).first():
                atelier = Atelier.query.filter_by(id=id_atelieru).first()
                flash(f'Uživatel {uzivatel.login} již spravuje atelier {atelier.nazev}', 'danger')
                return redirect(url_for('spravce_sprava'))
        else:
            # Vytvoření nového správce
            uzivatel.role = "spravce"
            db.session.commit()
            spravce_pridat(uzivatel)
                
        del uzivatel        # Je potřeba odstanit předchozí objekt, aby se mohl znovu načíst z databáze
        spravce = db.session.query(Spravce).filter_by(id=id_uzivatel).first()
        # Propojení správce a ateliéru
        db.session.execute(atelier_spravce.insert().values(id_atelier=id_atelieru, id_spravce=spravce.id_spravce))
        db.session.commit()
        return redirect(url_for('spravce_sprava'))

# Stránka pro správu jednotlivých uživatelů
@app.route('/admin/uzivatel/<int:id_uzivatele>', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def uzivatel_by_id(id_uzivatele):
    uzivatel = Uzivatel.query.filter_by(id=id_uzivatele).first_or_404()
    
    if request.method == 'GET':
        ateliery_uzivatel = db.session.query(Atelier).join(atelier_uzivatel, atelier_uzivatel.c.id_atelier == Atelier.id).filter(atelier_uzivatel.c.id_uzivatel == uzivatel.id).all() or []
        ateliery_vyucujici = []
        ateliery_spravce = []
        
        # Získání propojeni mezi ateliery a vyučujícím/správcem
        if uzivatel.role == "vyucujici":
            vyucujici = Vyucujici.query.filter_by(id=id_uzivatele).first()
            ateliery_vyucujici = db.session.query(Atelier).join(atelier_vyucujici, atelier_vyucujici.c.id_atelier == Atelier.id).filter(atelier_vyucujici.c.id_vyucujici == vyucujici.id_vyucujici).all()
        if uzivatel.role == "spravce":
            spravce = Spravce.query.filter_by(id=id_uzivatele).first()
            ateliery_spravce = db.session.query(Atelier).join(atelier_spravce, atelier_spravce.c.id_atelier == Atelier.id).filter(atelier_spravce.c.id_spravce == spravce.id_spravce).all()
        
        return render_template('admin/uzivatel_by_id.html', uzivatel=uzivatel, ateliery_vyucujici=ateliery_vyucujici, ateliery_uzivatel=ateliery_uzivatel, ateliery_spravce=ateliery_spravce)
    
    # Správa uživatelů - změna loginu
    elif request.method == 'POST' and "uzivatel_login" in request.form:
        novy_login = request.form.get('novy_login')
        if Uzivatel.query.filter_by(login=novy_login).first():
            flash('Uživatel s daným loginem již existuje', 'danger')
            return redirect(url_for('uzivatel_by_id', id_uzivatele=id_uzivatele))
        else:
            uzivatel.login = novy_login
            db.session.commit()
            flash('Login byl změněn', 'success')
        return redirect(url_for('uzivatel_by_id', id_uzivatele=id_uzivatele))
    
    # Změna hesla
    elif request.method == 'POST' and "uzivatel_heslo" in request.form:
        nove_heslo = request.form.get('nove_heslo')
        hashed_password = bcrypt.generate_password_hash(nove_heslo)
        uzivatel.heslo = hashed_password
        db.session.commit()
        flash('Heslo bylo změněno', 'success')
        return redirect(url_for('uzivatel_by_id', id_uzivatele=id_uzivatele))

    # Změna role
    elif request.method == 'POST' and 'uzivatel_role' in request.form:
        nova_role = request.form.get('nova_role')
        if nova_role == "vyucujici":
            if Vyucujici.query.filter_by(id=id_uzivatele).first():
                flash('Uživatel již je vyučující', 'danger')
                return redirect(url_for('uzivatel_by_id', id_uzivatele=id_uzivatele))
            else:
                vyucujici_pridat(uzivatel)
                # Pokud byl uživatel správcem, musí být odstraněn z tabulky Spravce
                if uzivatel.role == "spravce":
                    spravce_smazat(uzivatel)
                del uzivatel
                uzivatel = Uzivatel.query.filter_by(id=id_uzivatele).first()
                uzivatel.role = "vyucujici"
                db.session.commit()
        
        elif nova_role == "spravce":
            if Spravce.query.filter_by(id=id_uzivatele).first():
                flash('Uživatel již je správce', 'danger')
                return redirect(url_for('uzivatel_by_id', id_uzivatele=id_uzivatele))
            else:
                spravce_pridat(uzivatel)
                # Pokud byl uživatel vyučující, musí být odstraněn z tabulky Vyucujici
                if uzivatel.role == "vyucujici":
                    vyucujici_smazat(uzivatel)
                del uzivatel
                uzivatel = Uzivatel.query.filter_by(id=id_uzivatele).first()
                uzivatel.role = "spravce"
                db.session.commit()
        
        # Změna role na obyčejného uživatele
        else:
            if uzivatel.role == "uzivatel":
                flash('Uživatel již je obyčejným uživatelem', 'danger')
                return redirect(url_for('uzivatel_by_id', id_uzivatele=id_uzivatele))
            elif uzivatel.role == "vyucujici":
                vyucujici_smazat(uzivatel)
            elif uzivatel.role == "spravce":
                spravce_smazat(uzivatel)
            del uzivatel
            uzivatel = Uzivatel.query.filter_by(id=id_uzivatele).first()
            uzivatel.role = "uzivatel"
            db.session.commit()
        flash('Role byla změněna', 'success')
        return redirect(url_for('uzivatel_by_id', id_uzivatele=id_uzivatele))
    
    # Odstranění správce z ateliéru
    elif request.method == 'POST' and "spravce_atelier" in request.form:
        id_atelier = request.form.get('atelier_id')
        atelier_spravce_smazat(id_uzivatele, id_atelier)
        return redirect(url_for('uzivatel_by_id', id_uzivatele=id_uzivatele))

    # Odstranění vyučujícího z ateliéru
    elif request.method == 'POST' and "vyucujici_atelier" in request.form:
        id_atelier = request.form.get('atelier_id')
        atelier_vyucujici_smazat(id_uzivatele, id_atelier)
        return redirect(url_for('uzivatel_by_id', id_uzivatele=id_uzivatele))

    # Odstranění uživatele z ateliéru
    elif request.method == 'POST' and "uzivatel_atelier" in request.form:
        id_atelier = request.form.get('atelier_id')
        atelier_uzivatel_smazat(id_uzivatele, id_atelier)
        return redirect(url_for('uzivatel_by_id', id_uzivatele=id_uzivatele))
    
    # Smazání uživatele
    elif request.method == 'POST' and "delete_uzivatel" in request.form:
        db.session.delete(uzivatel)
        db.session.commit()
        flash('Uživatel byl smazán', 'success')
        return redirect(url_for('admin'))  
      
@app.route('/home')
def home():
    return render_template('home.html')

if __name__ == '__main__':
    app.run(debug=True)