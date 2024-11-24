#           -----------------  -----------------
#       Projekt do IIS - Umělecká škola
#       Autoři:
#        - Jakub Valeš, xvales04
#        - Petr Plíhal, xpliha02
#        - Martin Rybnikář, xrybni10
#                                     24.11.2024
#           -----------------  -----------------

from model import db, Vyucujici, Spravce, Atelier, atelier_vyucujici, atelier_uzivatel, atelier_spravce
from sqlalchemy import text

#           ----------------- Admin -----------------

#   --- Správa Atelierů ---
# Funkce pro přidání nového atelieru
def atelier_pridat(nazev):
    novy_atelier = Atelier()
    novy_atelier.nazev = nazev
    db.session.add(novy_atelier)
    db.session.commit()

# Funkce pro přidaní uživatele do tabulky spravce
def spravce_pridat(uzivatel):
    # Vytvoření nového záznamu v tabulce Spravce
    stmt = text("INSERT INTO spravce (id) VALUES (:id)")
    db.session.execute(stmt, {"id": uzivatel.id})
    db.session.commit()

# Funkce pro přidaní uživatele do tabulky vyucujici
def vyucujici_pridat(uzivatel):
    # Vytvoření nového záznamu v tabulce Vyucujici
    stmt = text("INSERT INTO vyucujici (id) VALUES (:id)")
    db.session.execute(stmt, {"id": uzivatel.id})
    db.session.commit()

# Smazání vyučujícího (ale ne uživatele)
def vyucujici_smazat(uzivatel):
    stmt = text("DELETE FROM vyucujici WHERE id = :id")
    db.session.execute(stmt, {"id": uzivatel.id})
    db.session.commit()

# Smazání správce (ale ne uživatele)    
def spravce_smazat(uzivatel):
    stmt = text("DELETE FROM spravce WHERE id = :id")
    db.session.execute(stmt, {"id": uzivatel.id})
    db.session.commit()
    
# Odebrání vyučujícího z atelieru
def atelier_vyucujici_smazat(id_uzivatele, id_atelier):
    id_vyucujici = Vyucujici.query.filter_by(id=id_uzivatele).first().id_vyucujici
    db.session.execute(
    atelier_vyucujici.delete().where(
        atelier_vyucujici.c.id_vyucujici == id_vyucujici,
        atelier_vyucujici.c.id_atelier == id_atelier
        )
    )
    db.session.commit()

# Odebrání správce z atelieru    
def atelier_spravce_smazat(id_uzivatele, id_atelier):
    id_spravce = Spravce.query.filter_by(id=id_uzivatele).first().id_spravce
    db.session.execute(
    atelier_spravce.delete().where(
        atelier_spravce.c.id_spravce == id_spravce,
        atelier_spravce.c.id_atelier == id_atelier
        )
    )
    db.session.commit()

# Odebrání uživatele z atelieru
def atelier_uzivatel_smazat(id_uzivatele, id_atelier):
    db.session.execute(
    atelier_uzivatel.delete().where(
        atelier_uzivatel.c.id_uzivatel == id_uzivatele,
        atelier_uzivatel.c.id_atelier == id_atelier
        )
    )
    db.session.commit()