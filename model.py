from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin
from sqlalchemy import text

# Vytvoreni SQLAlchemy instance pro databazi
db = SQLAlchemy()

# tabulka pro uzivatele, kteri si mohou vypujcit dane zarizeni
zarizeni_uzivatel = db.Table('zarizeni_uzivatel', db.metadata,
    db.Column('id_zarizeni', db.Integer, db.ForeignKey('zarizeni.id', ondelete='CASCADE')),
    db.Column('id_uzivatel', db.Integer, db.ForeignKey('uzivatel.id', ondelete='CASCADE'))
)

# Spojovaci tabulky pro vztahy N:N z ER diagramu
# Uzivatele spadajici pod dany atelier
atelier_uzivatel = db.Table('atelier_uzivatel', db.Model.metadata,
    db.Column('id_uzivatel', db.Integer, db.ForeignKey('uzivatel.id', ondelete='CASCADE')),
    db.Column('id_atelier', db.Integer, db.ForeignKey('atelier.id', ondelete='CASCADE'))
)

# Spravci daneho atelieru
atelier_spravce = db.Table('atelier_spravce', db.Model.metadata,
    db.Column('id_spravce', db.Integer, db.ForeignKey('spravce.id_spravce', ondelete='CASCADE')),
    db.Column('id_atelier', db.Integer, db.ForeignKey('atelier.id', ondelete='CASCADE'))
)

# Vyucujici daneho atelieru
atelier_vyucujici = db.Table('atelier_vyucujici', db.Model.metadata,
    db.Column('id_vyucujici', db.Integer, db.ForeignKey('vyucujici.id_vyucujici', ondelete='CASCADE')),
    db.Column('id_atelier', db.Integer, db.ForeignKey('atelier.id', ondelete='CASCADE'))
)

# Definice tabulek pro databazi pomoci trid
class Atelier(db.Model):
    __tablename__ = 'atelier'
    id = db.Column(db.Integer, primary_key=True)
    nazev = db.Column(db.String(50), unique=True, nullable=False)
    
    zarizeni = db.relationship('Zarizeni', back_populates='atelier', passive_deletes=True)                 # zarizeni atelieru
    uzivatele = db.relationship('Uzivatel', secondary=atelier_uzivatel, back_populates='ateliery')         # uzivatel spadajici do atelieru
    spravci = db.relationship('Spravce', secondary=atelier_spravce, back_populates='ateliery')             # spravce atelieru
    ucitele = db.relationship('Vyucujici', secondary=atelier_vyucujici, back_populates='ateliery')         # vyucujici z atelieru
    

class Uzivatel(db.Model, UserMixin):
    __tablename__ = 'uzivatel'
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(20), unique=True, nullable=False)
    jmeno = db.Column(db.String(50))
    email = db.Column(db.String(50))
    heslo = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False, default = 'uzivatel')     # admin/spravce/vyucujici/reg.uzivatel
    
    zarizeni = db.relationship('Zarizeni', secondary=zarizeni_uzivatel, back_populates='uzivatel', passive_deletes=True)      # seznam moznych pujcitelu
    ateliery = db.relationship('Atelier', secondary=atelier_uzivatel, back_populates='uzivatele')                             # ma pristup k atelieru
    rezervace = db.relationship('Rezervace', back_populates='uzivatel', passive_deletes=True)                                 # rezervace vytvorene uzivatelem
    
    # Vytvoreni generalizace/specializace pres atribut role
    __mapper_args__ = {
        'polymorphic_identity': 'uzivatel',
        'polymorphic_on': role
    }
    
class Vyucujici(Uzivatel):
    __tablename__ = 'vyucujici'
    id = db.Column(db.Integer, db.ForeignKey('uzivatel.id', ondelete='CASCADE'))
    id_vyucujici = db.Column(db.Integer, nullable=False, primary_key=True)
    
    ateliery = db.relationship('Atelier', secondary=atelier_vyucujici, back_populates='ucitele')
    zarizeni = db.relationship('Zarizeni', back_populates='vyucujici', passive_deletes=True)
    rezervace = db.relationship('Rezervace', back_populates='vyucujici', passive_deletes=True)

    # Specializace z Uzivatele
    __mapper_args__ = {
        'polymorphic_identity': 'vyucujici'
    }
    
class Spravce(Uzivatel):
    __tablename__ = 'spravce'
    id = db.Column(db.Integer, db.ForeignKey('uzivatel.id', ondelete='CASCADE'))
    id_spravce = db.Column(db.Integer, nullable=False, primary_key=True)
    
    ateliery = db.relationship('Atelier', secondary=atelier_spravce, back_populates='spravci')

    __mapper_args__ = {
        'polymorphic_identity': 'spravce'
    }

class Admin(Uzivatel):
    __tablename__ = 'admin'
    id = db.Column(db.Integer, db.ForeignKey('uzivatel.id', ondelete='CASCADE'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'admin'
    }


class Typ(db.Model):
    __tablename__ = 'typ'
    id = db.Column(db.Integer, primary_key=True)
    nazev = db.Column(db.String(50), unique=True, nullable=False)

    zarizeni = db.relationship('Zarizeni', back_populates='typ')


class Zarizeni(db.Model):
    __tablename__ = 'zarizeni'
    id = db.Column(db.Integer, primary_key=True)
    nazev = db.Column(db.String(100), nullable=False)
    rok_vyroby = db.Column(db.DateTime)
    datum_nakupu = db.Column(db.DateTime)
    max_doba_vypujcky = db.Column(db.Integer)   # Pocet dni
    povolene = db.Column(db.Boolean, default=True)
    id_atelier = db.Column(db.Integer, db.ForeignKey('atelier.id', ondelete='CASCADE'), nullable=False)
    id_typ = db.Column(db.Integer, db.ForeignKey('typ.id', ondelete='CASCADE'))
    id_vyucujici = db.Column(db.Integer, db.ForeignKey('vyucujici.id_vyucujici', ondelete='CASCADE'), nullable=False)
    #obrazek

    atelier = db.relationship('Atelier', back_populates='zarizeni')
    typ = db.relationship('Typ', back_populates='zarizeni')
    vyucujici = db.relationship('Vyucujici', back_populates='zarizeni')
    uzivatel = db.relationship('Uzivatel', secondary=zarizeni_uzivatel, back_populates='zarizeni')
    navraceni = db.relationship('Navraceni', back_populates='zarizeni', passive_deletes=True)
    rezervace = db.relationship('Rezervace', back_populates='zarizeni', passive_deletes=True)

class Navraceni(db.Model):
    __tablename__ = 'navraceni'
    id = db.Column(db.Integer, primary_key=True)
    id_zarizeni = db.Column(db.Integer, db.ForeignKey('zarizeni.id', ondelete='CASCADE'))
    vraceni = db.Column(db.String(10), nullable=False) # Vypujceni/Navraceni
    datum = db.Column(db.DateTime, nullable=False)

    zarizeni = db.relationship('Zarizeni', back_populates='navraceni')                                 # patri k danemu zarizeni
    
class Rezervace(db.Model):
    __tablename__ = 'rezervace'
    id = db.Column(db.Integer, primary_key=True)
    stav = db.Column(db.String(20), nullable=False)  # Rezervováno, Vypujceno, Vraceno
    datum_od = db.Column(db.DateTime, nullable=False)
    datum_do = db.Column(db.DateTime, nullable=False)
    id_zarizeni = db.Column(db.Integer, db.ForeignKey('zarizeni.id', ondelete='CASCADE'), nullable=False)
    id_uzivatel = db.Column(db.Integer, db.ForeignKey('uzivatel.id', ondelete='CASCADE'), nullable=False)
    id_vyucujici = db.Column(db.Integer, db.ForeignKey('vyucujici.id_vyucujici', ondelete='CASCADE'), nullable=False)


    zarizeni = db.relationship('Zarizeni', back_populates='rezervace')
    uzivatel = db.relationship('Uzivatel', back_populates='rezervace')
    vyucujici = db.relationship('Vyucujici', back_populates='rezervace', foreign_keys=[id_vyucujici]) # bez foreign_keys to hazelo error idk
    
# Funkce pro naplneni databaze ukazkovymi daty
def insert_data(bcrypt):
    typy = [
        Typ(nazev='Počítačové vybavení'),
        Typ(nazev='Kamery'),
        Typ(nazev='Mikrofony'),
        Typ(nazev='Osvětlení'),
    ]
    ateliery = [
        Atelier(nazev='Filmový atelier'),
        Atelier(nazev='Architektonický atelier'),
        Atelier(nazev='Fotografický ateliér'),
        Atelier(nazev='Výtvarný ateliér'),
    ]
    uzivatele = [
        Spravce(   id = 1,  login='spravce1', jmeno='Samuel Stejskal',     email='samuel.stejskal@umelecka-skola.cz',     heslo=bcrypt.generate_password_hash('aaa'), role='spravce',   id_spravce=10),
        Vyucujici( id = 2,  login='vyucuj1',  jmeno='Václav Vávra',        email='vaclav.vavra@umelecka-skola.cz',        heslo=bcrypt.generate_password_hash('aaa'), role='vyucujici', id_vyucujici=100),
        Vyucujici( id = 3,  login='vyucuj2',  jmeno='Veronika Veselá',     email='veronika.vesela@umelecka-skola.cz',     heslo=bcrypt.generate_password_hash('aaa'), role='vyucujici', id_vyucujici=101),
        Uzivatel(  id = 4,  login='user1',    jmeno='Radek Rous',          email='radek.rous@umelecka-skola.cz',          heslo=bcrypt.generate_password_hash('aaa'), role='uzivatel'),
        Uzivatel(  id = 5,  login='user2',    jmeno='Radislav Růžek',      email='radislav.ruzek@umelecka-skola.cz',      heslo=bcrypt.generate_password_hash('aaa'), role='uzivatel'),
        Uzivatel(  id = 6,  login='user3',    jmeno='Radomíra Richterová', email='radomira.richterova@umelecka-skola.cz', heslo=bcrypt.generate_password_hash('aaa'), role='uzivatel'),
        Admin(     id = 100, login='admin',   jmeno='Adam Anderle',        email='adam.anderle@umelecka-skola.cz',        heslo=bcrypt.generate_password_hash('aaa'), role='admin'),
    ]
    
    zarizeni = [
        Zarizeni(nazev = 'Notebook Lenovo', rok_vyroby = datetime(2021, 9, 14), datum_nakupu = datetime(2021, 12, 12), max_doba_vypujcky = 10, id_atelier = 1, id_typ = 1, id_vyucujici = 100),
        Zarizeni(nazev = 'GoPro HERO10', rok_vyroby = datetime(2023, 1, 11), datum_nakupu = datetime(2024, 5, 5), max_doba_vypujcky = 20, id_atelier = 1, id_typ = 2, id_vyucujici = 100),
        Zarizeni(nazev = 'Shure SM7db', rok_vyroby = datetime(2023, 2, 2), datum_nakupu = datetime(2023, 7, 10), max_doba_vypujcky = 30, id_atelier = 1, id_typ = 3, id_vyucujici = 100),
        Zarizeni(nazev = 'Elgato Ring Light', rok_vyroby = datetime(2024, 1, 5), datum_nakupu = datetime(2024, 1, 6), max_doba_vypujcky = 100, id_atelier = 1, id_typ = 4, id_vyucujici = 100),
        Zarizeni(nazev = 'Elgato Ring Light', rok_vyroby = datetime(2024, 1, 5), datum_nakupu = datetime(2024, 1, 10), max_doba_vypujcky = 100, id_atelier = 3, id_typ = 4, id_vyucujici = 101),
        Zarizeni(nazev = 'Reproduktory Marhall Acton', rok_vyroby = datetime(2023, 1, 1), datum_nakupu = datetime(2023, 1, 10), max_doba_vypujcky = 90, id_atelier = 1, id_typ = 1, id_vyucujici = 100),
        Zarizeni(nazev = 'Notebook MacBook Air', rok_vyroby = datetime(2023, 1, 1), datum_nakupu = datetime(2023, 1, 10), max_doba_vypujcky = 300, id_atelier = 1, id_typ = 1, id_vyucujici = 100),
        Zarizeni(nazev = 'Kamera SONY ABC2', rok_vyroby = datetime(2023, 1, 1), datum_nakupu = datetime(2024, 1, 1), max_doba_vypujcky = 300, id_atelier = 1, id_typ = 2, id_vyucujici = 100),
        Zarizeni(nazev = 'Notebook MacBook Air', rok_vyroby = datetime(2020, 1, 1), datum_nakupu = datetime(2021, 12, 12), max_doba_vypujcky = 300, id_atelier = 2, id_typ = 1, id_vyucujici = 100),
        Zarizeni(nazev = 'LED pásky', rok_vyroby = datetime(2020, 1, 1), datum_nakupu = datetime(2022, 7, 11), max_doba_vypujcky = 70, id_atelier = 2, id_typ = 4, id_vyucujici = 100),
    ]
    
    navraceni = [
        Navraceni(id_zarizeni = 1, vraceni = 'Vypujceni', datum = datetime(2025, 1, 1)),
        Navraceni(id_zarizeni = 2, vraceni = 'Vypujceni', datum = datetime(2025, 2, 1)),
        Navraceni(id_zarizeni = 3, vraceni = 'Vypujceni', datum = datetime(2025, 2, 1)),
        Navraceni(id_zarizeni = 4, vraceni = 'Vypujceni', datum = datetime(2025, 1, 1)),
        Navraceni(id_zarizeni = 5, vraceni = 'Navraceni', datum = datetime.now()),
        Navraceni(id_zarizeni = 1, vraceni = 'Navraceni', datum = datetime(2025, 1, 1)),
        Navraceni(id_zarizeni = 1, vraceni = 'Navraceni', datum = datetime(2024, 12, 23)),
    ]
    
    rezervace = [
        Rezervace(stav = 'Vypujceno', datum_od = datetime(2024, 10, 1), datum_do = datetime(2025, 1, 1), id_zarizeni = 1, id_uzivatel = 4, id_vyucujici = 100),
        Rezervace(stav = 'Vypujceno', datum_od = datetime(2024, 10, 1), datum_do = datetime(2025, 2, 1), id_zarizeni = 2, id_uzivatel = 4, id_vyucujici = 100),
        Rezervace(stav = 'Rezervovano', datum_od = datetime(2024, 11, 1), datum_do = datetime(2025, 2, 1), id_zarizeni = 3, id_uzivatel = 4, id_vyucujici = 100),
        Rezervace(stav = 'Rezervovano', datum_od = datetime(2024, 11, 1), datum_do = datetime(2025, 1, 1), id_zarizeni = 4, id_uzivatel = 5, id_vyucujici = 101),
        Rezervace(stav = 'Vraceno', datum_od = datetime(2023, 1, 10), datum_do = datetime(2023, 1, 30), id_zarizeni = 6, id_uzivatel = 4, id_vyucujici = 100),
        Rezervace(stav = 'Vraceno', datum_od = datetime(2023, 1, 12), datum_do = datetime(2023, 2, 1), id_zarizeni = 7, id_uzivatel = 4, id_vyucujici = 100),
        Rezervace(stav = 'Vraceno', datum_od = datetime(2023, 11, 12), datum_do = datetime(2023, 12, 12), id_zarizeni = 6, id_uzivatel = 4, id_vyucujici = 100),
        Rezervace(stav = 'Vraceno', datum_od = datetime(2023, 11, 12), datum_do = datetime(2023, 12, 1), id_zarizeni = 8, id_uzivatel = 4, id_vyucujici = 100),
        Rezervace(stav = 'Rezervovano', datum_od = datetime(2025, 1, 1), datum_do = datetime(2025, 2, 1), id_zarizeni = 3, id_uzivatel = 4, id_vyucujici = 100),
        Rezervace(stav = 'Rezervovano', datum_od = datetime(2025, 1, 1), datum_do = datetime(2025, 2, 1), id_zarizeni = 4, id_uzivatel = 4, id_vyucujici = 100),
        Rezervace(stav = 'Vypujceno', datum_od = datetime(2024, 11, 13), datum_do = datetime(2025, 1, 1), id_zarizeni = 2, id_uzivatel = 4, id_vyucujici = 100),
        Rezervace(stav = 'Vypujceno', datum_od = datetime(2024, 11, 13), datum_do = datetime(2025, 1, 1), id_zarizeni = 7, id_uzivatel = 4, id_vyucujici = 100),
        
    ]
    
    # Propojeni uzivatelu s prislusnymi ateliery
    # Pro správce/vyučující se přidají do tabulky atelier_spravce/atelier_vyucujici
    uzivatele[0].ateliery.append(ateliery[0])
    uzivatele[1].ateliery.append(ateliery[0])
    uzivatele[1].ateliery.append(ateliery[1])
    uzivatele[1].ateliery.append(ateliery[2])
    uzivatele[2].ateliery.append(ateliery[2])
    
    # Přidání obyčejných uživatelů do ateliérů, funguje takhle bez problémů
    uzivatele[3].ateliery.append(ateliery[0])
    uzivatele[3].ateliery.append(ateliery[1])
    uzivatele[4].ateliery.append(ateliery[2])
    uzivatele[5].ateliery.append(ateliery[2])
    uzivatele[5].ateliery.append(ateliery[0])
    
    # Pridani samotnych dat do databaze
    db.session.add_all(typy)
    db.session.add_all(ateliery)
    db.session.add_all(uzivatele)
    db.session.add_all(zarizeni)
    db.session.add_all(navraceni)
    db.session.add_all(rezervace)
    
    db.session.commit()
    
    # Po commitu, lze přidat vyučující/správce i jako obyčejné uživatele do ateliérů (aby si také mohli vypujčovat zařízení)
    db.session.execute(atelier_uzivatel.insert().values(id_atelier=ateliery[0].id, id_uzivatel=uzivatele[0].id))
    db.session.execute(atelier_uzivatel.insert().values(id_atelier=ateliery[0].id, id_uzivatel=uzivatele[1].id))
    db.session.execute(atelier_uzivatel.insert().values(id_atelier=ateliery[1].id, id_uzivatel=uzivatele[1].id))
    db.session.execute(atelier_uzivatel.insert().values(id_atelier=ateliery[2].id, id_uzivatel=uzivatele[1].id))
    db.session.execute(atelier_uzivatel.insert().values(id_atelier=ateliery[2].id, id_uzivatel=uzivatele[2].id))
    db.session.commit()
    
# Zkouska funkcnosti CASCADE pri odstraneni zaznamu
def delete_one():
    db.session.query(Zarizeni).filter(Zarizeni.id == 1).delete()
    db.session.commit()