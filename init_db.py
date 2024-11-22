from app import app, db, bcrypt
from sqlalchemy import inspect
from model import insert_data

# Skript pro inicializaci databáze a naplnění daty
# spuštění: python3 init_db.py

# Funkce pro kontrolu existence tabulek v databázi
def kontrola_existence(engine):
    inspector = inspect(engine)
    tabulky = inspector.get_table_names()
    return len(tabulky) > 0

with app.app_context():
    # Pokud tabulky existují, smažeme je
    if kontrola_existence(db.engine):
        print("Exitující tabulky byly smazány.")
        db.drop_all()

    db.create_all()
    insert_data(bcrypt)
    print("Databáze byla inicializována.")