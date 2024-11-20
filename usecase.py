from datetime import datetime
from model import db, Uzivatel, Rezervace, Zarizeni, Typ, Atelier, zarizeni_uzivatel
from sqlalchemy import or_

# Pro hashování hesel
from werkzeug.security import check_password_hash

#           ---------- Neregistrovaný uživatel ----------

# Funkce pro přidání zaregistrovaného uživatele do databáze s rolí obyčejného uživatele
def zaregistrovat_se(login, heslo):
    pridani_uzivatele(login=login, heslo=heslo)

#           ----------- Registrovaný uživatel -----------

# Upravení profilu (loginu nebo hesla)
def upraveni_profilu(id_uzivatele, novy_login=None, nove_heslo=None):
    uprava_uzivatele(id_uzivatele, novy_login=novy_login, nove_heslo=nove_heslo)

# Sledování výpůjček
def sledovani_vypujcek(id_uzivatele):
    return Rezervace.query.filter_by(id_uzivatel=id_uzivatele).all()

# Vrátí všechny aktivní výpůjčky uživatele (-> stav "Rezervováno" nebo "Vypůjčeno")
def ziskat_aktivni_vypujcky(id_uzivatele):
    return Rezervace.query.filter_by(id_uzivatel=id_uzivatele).filter(Rezervace.stav.in_(["Rezervováno", "Vypůjčeno"])).all()

# Vrátí všechny výpůjčky uživatele, které již byly vráceny (-> stav "Vraceno")
def ziskat_vracene_vypujcky(id_uzivatele):
    return Rezervace.query.filter_by(id_uzivatel=id_uzivatele).filter(Rezervace.stav == "Vraceno").all()

# Funkce pro rezervaci zařízení (funkce nekontroluje, zda není zařízení již rezervováno)
def rezervace_zarizeni(id_zarizeni, id_uzivatele, datum_od, datum_do):
    
    # TODO: Měla by být kontrola na vypůjčítelnost zařízení tady, nebo v app.py?

    zarizeni = Zarizeni.query.get(id_zarizeni)

    nova_rezervace = Rezervace(
        stav="Rezervovano",
        datum_od=datum_od,
        datum_do=datum_do,
        id_zarizeni=id_zarizeni,
        id_uzivatel=id_uzivatele,
        # id_zarizeni je předáno jako číslo, ne objekt -> nelze se odkazovat na parametry objektu, nejdřív se můsí získát objekt
        #id_vyucujici=id_zarizeni.id_vyucujici
        id_vyucujici=zarizeni.id_vyucujici
    )
    db.session.add(nova_rezervace)
    db.session.commit()

# Funkce pro vypůjčení zařízení (funkce nekontroluje, zda není zařízení již vypůjčeno)
def vypujceni_zarizeni(id_zarizeni, id_uzivatele, id_vyucujici, datum_od, datum_do):
    nova_vypujcka = Rezervace(
        stav="Vypůjčeno",
        datum_od=datum_od,
        datum_do=datum_do,
        id_zarizeni=id_zarizeni,
        id_uzivatel=id_uzivatele,
        id_vyucujici=id_vyucujici
    )
    db.session.add(nova_vypujcka)
    db.session.commit()

# Zjistí stav konkrétního zařízení (Rezervováno, Vypujceno, Vraceno) pro daného uživatele
def zjisteni_stavu_zarizeni(id_zarizeni, id_uzivatele):
    rezervace = Rezervace.query.filter_by(id_zarizeni=id_zarizeni, id_uzivatel=id_uzivatele).first()
    if rezervace:
        return rezervace.stav
    return None

# Určí, zda si uživatel může vypůjčit dané zařízení
# TODO: oddělit moze_rezervovat_zarizeni a muze_zobrazit_zarizeni (I když zařízení není povoleno, může být zobrazeno)
def muze_rezervovat_zarizeni(id_zarizeni, id_uzivatele):

    zarizeni = Zarizeni.query.get(id_zarizeni)

    # Uživatel musí být v ateliéru, ve kterém je zařízení
    if zarizeni and zarizeni.id_atelier in [atelier.id for atelier in ziskat_ateliery_uzivatele(id_uzivatele)]:

        # Dále musí být zařízení povolené, nebo musí existovat záznam o povolení v tabulce zarizeni_uzivatel pro dané zařízení a uživatele
        if zarizeni.povolene or zarizeni_uzivatel.query.filter_by(id_zarizeni=id_zarizeni, id_uzivatel=id_uzivatele).first():
            return True

    return False

# Určí, zda si uživatel může vypůjčit dané zařízení - z hlediska kolizí s jinými rezervacemi a logikou časových intervalů
def je_validni_datum_rezervace(datum_od, datum_do, id_zarizeni):
    '''
    - Pro datum musí platit: (je_validni_datum_rezervace())
        - Ani jedno z datumů nesmí být prázdné, nebo v minulosti
        - Data nemůžou být stejná
        - Datum začátku musí být dříve než datum konce
        - Počet dní, do kterých zařízení zasahuje, nesmí být větší než maximální počet dní, na které lze zařízení vypůjčit
        - Rezervace nesmí být v konfliktu s jinou rezervací

    TODO: nějáké zprávy o tom, co je na datu špatně
    '''
    if not datum_od or not datum_do:
        return False
    
    # Kontrola, zda datum_od a datum_do nejsou v minulosti
    if datum_od < datetime.now() or datum_do < datetime.now():
        return False
    
    # Kontrola, zda datum_od a datum_do nejsou stejné
    if datum_od == datum_do:
        return False
    
    # Kontrola, zda datum_od je menší než datum_do
    if datum_od >= datum_do:
        return False
    
    # Kontrola, zda rezervace nepřesahuje maximální počet dní, na které lze zařízení vypůjčit
    zarizeni = Zarizeni.query.get(id_zarizeni)
    if (datum_do - datum_od).days > zarizeni.max_doba_vypujcky:
        return False
    
    # Kontorla, zda rezervace není v konfliktu s jinou rezervací - berou se v pouze rezervace, které nemají stav Vraceno
    rezervace = Rezervace.query.filter_by(id_zarizeni=id_zarizeni).filter(Rezervace.stav != "Vraceno").all()

    for r in rezervace:
        if r.datum_od < datum_do and r.datum_do > datum_od:
            return False
    

    return True

# Vrátí všechny ateliéry, ve kterých je uživatel přihlášen
def ziskat_ateliery_uzivatele(id_uzivatele):
    uzivatel = Uzivatel.query.get(id_uzivatele)
    if not uzivatel:
        return []
    return uzivatel.ateliery

''' 
    Funkce pro vyhledání zařízení podle různých kritérií

    V případě zadání id_zarizeni, vrátí jeden záznam, místo seznamu, nehledě na další parametry

    Všechny parametry jsou nepovinné -> ve výchozím volání vrátí všechna zařízení
'''
def hledani_zarizeni(id_zarizeni=None, nazev=None, id_typ=None, id_atelier=None, id_uzivatele=None, pouze_vypujcitelne=False):
    zarizeni = Zarizeni.query

    # id_zarizeni je primární klíč -> více jak jeden záznam nemůže existovat
    if id_zarizeni:
        zarizeni = zarizeni.filter_by(id=id_zarizeni)
        return zarizeni.first()

    if pouze_vypujcitelne:

        # Uživtel si může vypůjčit pouze zařízení z ateliérů, ve kterých je přihlášen
        uzivatelovy_ateliery = ziskat_ateliery_uzivatele(id_uzivatele)
        zarizeni = zarizeni.filter(Zarizeni.id_atelier.in_([atelier.id for atelier in uzivatelovy_ateliery]))

        # Vypůjčitelné zařízení dále musí mít atribut povolené na true, nebo musí existovat záznam o povolení vypůjčení v tabulce zarizeni_uzivatel pro dané zařízení a uživatele
        zarizeni = zarizeni.outerjoin(zarizeni_uzivatel, Zarizeni.id == zarizeni_uzivatel.c.id_zarizeni).filter(
            or_(
                Zarizeni.povolene == True,
                zarizeni_uzivatel.c.id_uzivatel == id_uzivatele
            )
        )
    
    if nazev:
        zarizeni = zarizeni.filter(Zarizeni.nazev.ilike(f"%{nazev}%"))
    if id_typ:
        zarizeni = zarizeni.filter_by(id_typ=id_typ)
    if id_atelier:
        zarizeni = zarizeni.filter_by(id_atelier=id_atelier)
        
    return zarizeni.all()

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
