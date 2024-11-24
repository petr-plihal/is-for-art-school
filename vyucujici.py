#           -----------------  -----------------
#       Projekt do IIS - Umělecká škola
#       Autoři:
#        - Jakub Valeš, xvales04
#        - Petr Plíhal, xpliha02
#        - Martin Rybnikář, xrybni10
#                                     24.11.2024
#           -----------------  -----------------

from datetime import datetime
from model import db, Zarizeni, zarizeni_uzivatel, Vyucujici, Navraceni, Uzivatel

#           ----------------- Vyučující -----------------

#   --- Správa zařízení ---
# Funkce pro přidání nového zařízení
def pridat_zarizeni(nazev, id_atelier, rok_vyroby, datum_nakupu, doba_vypujcky, id_typ, id_vyucujici):
    nove_zarizeni = Zarizeni()
    nove_zarizeni.nazev = nazev
    nove_zarizeni.rok_vyroby = rok_vyroby
    nove_zarizeni.datum_nakupu = datum_nakupu
    nove_zarizeni.max_doba_vypujcky = doba_vypujcky
    nove_zarizeni.id_atelier = id_atelier
    nove_zarizeni.id_typ = id_typ
    nove_zarizeni.id_vyucujici = id_vyucujici
    
    db.session.add(nove_zarizeni)
    db.session.commit()
    
    return nove_zarizeni.id

# Funkce pro odstranění zařízení
def odstraneni_zarizeni(id_zarizeni):
    zarizeni = Zarizeni.query.get(id_zarizeni)
    if zarizeni:
        db.session.delete(zarizeni)
        db.session.commit()

# Funkce pro aktualizaci existujícího zařízení
def aktualizace_zarizeni(id_zarizeni, novy_nazev=None, novy_typ=None, rok_vyroby=None, datum_nakupu=None, max_doba_vypujcky=None):
    zarizeni = Zarizeni.query.get(id_zarizeni)
    if zarizeni:
        if novy_nazev:
            zarizeni.nazev = novy_nazev
        if novy_typ:
            zarizeni.id_typ = novy_typ
        if datum_nakupu:
            zarizeni.datum_nakupu = datum_nakupu
        if rok_vyroby:
            zarizeni.rok_vyroby = rok_vyroby
        if max_doba_vypujcky:
            zarizeni.max_doba_vypujcky = max_doba_vypujcky
        db.session.commit()

# Funkce pro přidání data vrácení/vypůjčení
def pridani_vraceni(id_zarizeni, typ=None, datum_vraceni=None):
        nove_navraceni = Navraceni()
        nove_navraceni.id_zarizeni = id_zarizeni
        nove_navraceni.vraceni = typ
        nove_navraceni.datum = datum_vraceni
        db.session.add(nove_navraceni)
        db.session.commit()
# ------

def odstraneni_navraceni(id_zarizeni):
    while Navraceni.query.filter_by(id_zarizeni=id_zarizeni).first():
        date_to_delete = Navraceni.query.filter_by(id_zarizeni=id_zarizeni).first()
        db.session.delete(date_to_delete)
        db.session.commit()

# ---- Správa seznamů skupin vypůjčení ateliéru ----

# Funkce pro přidání vztahu mezi zařízením a uživatelem
def pridat_zaznam_zarizeni_uzivatel(id_zarizeni, id_uzivatel):
    # Ověření, zda záznam již existuje
    existujici_zaznam = db.session.query(zarizeni_uzivatel).filter_by(id_zarizeni=id_zarizeni, id_uzivatel=id_uzivatel).first()

    if not existujici_zaznam:
        novy_zaznam = zarizeni_uzivatel.insert().values(id_zarizeni=id_zarizeni, id_uzivatel=id_uzivatel)
        db.session.execute(novy_zaznam)
        db.session.commit()

def odebrat_zaznam_zarizeni_uzivatel(id_zarizeni, id_uzivatel):
    db.session.execute(
        zarizeni_uzivatel.delete().where(
            zarizeni_uzivatel.c.id_zarizeni == id_zarizeni, 
            zarizeni_uzivatel.c.id_uzivatel == id_uzivatel
            )
    )
    db.session.commit()


# Funkce pro kontrolu, zda je zařízení v nějakém vztahu s libovolným uživatelem
def ma_zarizeni_zaznamy(id_zarizeni):
    # Dotaz na první záznam, který odpovídá id_zarizeni
    existuje_zaznam = db.session.query(zarizeni_uzivatel).filter_by(id_zarizeni=id_zarizeni).first() is not None
    return existuje_zaznam

# Funkce pro kontrolu zdali, má daný uživatel přístup na stránku
def kontrola_pristupu_vyucujici(user_id, id_zarizeni):
    uzivatel = Uzivatel.query.filter_by(id=user_id).first_or_404()
    if uzivatel.role == 'admin':
        return True
    del uzivatel
    vyucujici = Vyucujici.query.filter_by(id=user_id).first_or_404()
    zarizeni = Zarizeni.query.filter_by(id=id_zarizeni).first_or_404()
    
    return zarizeni.id_vyucujici == vyucujici.id_vyucujici

def format_datum(datum):
    # Typ datetime je ve formátu YYYY-MM-DD-THH:MM, takže jej potřebujeme rozdělit a vrátit v požadovaném formátu
    date_part, time_part = datum.split('T')
    date_parts = date_part.split('-')
    time_parts = time_part.split(':')
    datum_parts = [int(part) for part in date_parts + time_parts]
    datum = datetime(datum_parts[0], datum_parts[1], datum_parts[2], datum_parts[3], datum_parts[4])
    return datum

def get_users_devices(id_vyucujici):
    devices = Zarizeni.query.filter_by(id_vyucujici=id_vyucujici).all()
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