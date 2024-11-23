from datetime import datetime
from model import db, Uzivatel, Rezervace, Zarizeni, zarizeni_uzivatel
from usecase import uprava_uzivatele
from sqlalchemy import or_
from sqlalchemy.orm import aliased

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

        zarizeni_uzivatel_alias = aliased(zarizeni_uzivatel) # Vytvoření aliasu pro tabulku zarizeni_uzivatel
        
        # Provádění outer join mezi tabulkou Zarizeni a aliasem zarizeni_uzivatel_alias
        zarizeni = zarizeni.outerjoin(zarizeni_uzivatel_alias, Zarizeni.id == zarizeni_uzivatel_alias.c.id_zarizeni).filter(
            or_(
                # Filtrace zařízení, která mají atribut povolené na true
                Zarizeni.povolene == True,
                # Nebo filtrace zařízení, která mají záznam v tabulce zarizeni_uzivatel pro daného uživatele
                zarizeni_uzivatel_alias.c.id_uzivatel == id_uzivatele
            )
        )
    
    if nazev:
        zarizeni = zarizeni.filter(Zarizeni.nazev.ilike(f"%{nazev}%"))
    if id_typ:
        zarizeni = zarizeni.filter(Zarizeni.id_typ == id_typ)
    if id_atelier:
        zarizeni = zarizeni.filter(Zarizeni.id_atelier == id_atelier)
        
    return zarizeni.all()
