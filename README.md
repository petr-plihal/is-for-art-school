# IIS_projekt
IIS Projekt - Umělecká škola

# Instalace a spuštění
## Předpoklady
- Python 3.6+
- MySQL server

## Instalace
1. Stáhněte si repozitář
2. Vytvořtě databázi a uživatele s právy k databázi v MySQL serveru 
(přihlašovací údaje do databáze je potřeba zadat do souboru `app.py` `app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://<username>:<password>@<host>/<database>'`, v případě lokální databáze)
3. Vytvořte virtuální prostředí
    - `pip3 install virtualenv`
    - `virtualenv env`
    - `source env/bin/activate`
4. Nainstalujte závislosti
    - `pip3 install flask flask-sqlalchemy pymysql flask-bcrypt flask-login cryptography`
    - nebo
    - `pip install -r requirements.txt`
5. Spusťte aplikaci
    - `python3 app.py`
    - nebo
    - `flask run`
Aplikace je pak dostupná přes localhost na portu 5000

## Ukazkoví uživatelé
### Loginy
- Admin: admin
- Správci: spravce1
- Učitele: vyucuj1, vyucuj2
- Uživatele: user1, user2, user3
### Heslo pro všechny
- aaa