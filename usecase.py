from datetime import datetime
from model import db, Uzivatel, Rezervace, Zarizeni, Typ, Atelier, zarizeni_uzivatel
from sqlalchemy import or_

# Pro hashování hesel
from werkzeug.security import check_password_hash

#           ---------- Neregistrovaný uživatel ----------

# Funkce pro přidání zaregistrovaného uživatele do databáze s rolí obyčejného uživatele
def zaregistrovat_se(login, heslo):
    pridani_uzivatele(login=login, heslo=heslo)


#           ----------------- Vyučující -----------------

#   --- Správa zařízení ---
# Funkce pro přidání nového zařízení
def pridat_zarizeni(nazev, id_typ, id_atelier):
    nove_zarizeni = Zarizeni(
        nazev=nazev,
        id_typ=id_typ,
        id_atelier=id_atelier
    )
    db.session.add(nove_zarizeni)
    db.session.commit()

# Funkce pro odstranění zařízení
def odstraneni_zarizeni(id_zarizeni):
    zarizeni = Zarizeni.query.get(id_zarizeni)
    if zarizeni:
        db.session.delete(zarizeni)
        db.session.commit()

# Funkce pro aktualizaci existujícího zařízení
def aktualizace_zarizeni(id_zarizeni, novy_nazev=None, novy_typ=None, novy_atelier=None):
    zarizeni = Zarizeni.query.get(id_zarizeni)
    if zarizeni:
        if novy_nazev:
            zarizeni.nazev = novy_nazev
        if novy_typ:
            zarizeni.id_typ = novy_typ
        if novy_atelier:
            zarizeni.id_atelier = novy_atelier
        db.session.commit()
# ------

# ---- Správa seznamů skupin vypůjčení ateliéru ----

# Funkce pro přidání vztahu mezi zařízením a uživatelem
def pridat_zaznam_zarizeni_uzivatel(id_zarizeni, id_uzivatel):
    # Ověření, zda záznam již existuje
    existujici_zaznam = db.session.query(zarizeni_uzivatel).filter_by(id_zarizeni=id_zarizeni, id_uzivatel=id_uzivatel).first()

    if not existujici_zaznam:
        novy_zaznam = zarizeni_uzivatel.insert().values(id_zarizeni=id_zarizeni, id_uzivatel=id_uzivatel)
        db.session.add(novy_zaznam)
        db.session.commit()

# Funkce pro kontrolu, zda je zařízení v nějakém vztahu s libovolným uživatelem
def ma_zarizeni_zaznamy(id_zarizeni):
    # Dotaz na první záznam, který odpovídá id_zarizeni
    existuje_zaznam = db.session.query(zarizeni_uzivatel).filter_by(id_zarizeni=id_zarizeni).first() is not None
    return existuje_zaznam

#           ------------- Správce ateliéru -------------

# ---- Správa typů zařízení ----
# Funkce pro přidání nového typu zařízení
def pridani_typu(nazev):
    novy_typ = Typ(nazev=nazev)
    db.session.add(novy_typ)
    db.session.commit()

# Funkce pro aktualizaci názvu typu zařízení
def aktualizace_typu(id_typu, novy_nazev):
    typ = Typ.query.get(id_typu)
    if typ:
        typ.nazev = novy_nazev
        db.session.commit()

# Funkce pro odstranění typu zařízení
def odstraneni_typu(id_typu):
    typ = Typ.query.get(id_typu)
    if typ:
        db.session.delete(typ)
        db.session.commit()

# Funkce pro získání všech typů zařízení
def ziskat_vsechny_typy():
    return Typ.query.all()
# --------

# Funkce pro povýšení registrovaného uživatele na vyučujícího
def povyseni_na_vyucujici(id_uzivatele):
    uzivatel = Uzivatel.query.get(id_uzivatele)
    if uzivatel:
        uzivatel.role = "vyucujici"
        db.session.commit()

#           ------------------- Admin -------------------

# ---- Správa uživatelů ----
# Přidání nového uživatele
def pridani_uzivatele(login, heslo, role="uzivatel"):
    novy_uzivatel = Uzivatel(login=login, heslo=heslo, role=role)
    db.session.add(novy_uzivatel)
    db.session.commit()

# Aktualizace uživatelských údajů
def uprava_uzivatele(id_uzivatele, novy_login=None, nove_heslo=None, nova_role=None):
    uzivatel = Uzivatel.query.get(id_uzivatele)
    if uzivatel:
        if novy_login:
            uzivatel.login = novy_login
        if nove_heslo:
            uzivatel.heslo = nove_heslo
        if nova_role:
            uzivatel.role = nova_role
        db.session.commit()

# Odstranění uživatele
def odstraneni_uzivatele(id_uzivatele):
    uzivatel = Uzivatel.query.get(id_uzivatele)
    if uzivatel:
        db.session.delete(uzivatel)
        db.session.commit()

# Získání seznamu všech uživatelů
def seznam_uzivatelu():
    return Uzivatel.query.all()
# --------

# ----- Správa ateliérů -----
# Přidání nového ateliéru
def pridani_atelieru(nazev, popis=None):
    novy_atelier = Atelier(nazev=nazev, popis=popis)
    db.session.add(novy_atelier)
    db.session.commit()

# Aktualizace existujícího ateliéru
def uprava_atelieru(id_atelieru, novy_nazev=None, novy_popis=None):
    atelier = Atelier.query.get(id_atelieru)
    if atelier:
        if novy_nazev:
            atelier.nazev = novy_nazev
        if novy_popis:
            atelier.popis = novy_popis
        db.session.commit()

# Odstranění ateliéru
def odstraneni_atelieru(id_atelieru):
    atelier = Atelier.query.get(id_atelieru)
    if atelier:
        db.session.delete(atelier)
        db.session.commit()

# Získání seznamu všech ateliérů
def seznam_atelieru():
    return Atelier.query.all()
# ----------

# Povýšení registrovaného uživatele na správce ateliéru
def povyseni_na_spravce_atelieru(id_uzivatele):
    uzivatel = Uzivatel.query.get(id_uzivatele)
    if uzivatel:
        uzivatel.role = "spravce"
        db.session.commit()


# Přihlášení uživatele - vrátí buď objekt uživatele (pro další práci) nebo None při neshodě
def over_login(login, heslo):

    # Získání uživatele podle loginu
    uzivatel = Uzivatel.query.filter_by(login=login).first()

    # Kontrola hesla
    if uzivatel and uzivatel.heslo == heslo: #check_password_hash(uzivatel.heslo, heslo):
        return uzivatel
    return None
