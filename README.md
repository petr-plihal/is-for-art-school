# IIS_projekt
IIS Projekt - Umělecká škola

# Prvni spusteni
## Stazeni a spusteni virtual env
pip3 install virtualenv
virtualenv env
source env/bin/activate

## Pridani balicku do virtualenv
pip3 install flask flask-sqlalchemy pymysql

## Samotne spusteni aplikace
python3 app.py
## Aplikace je pak dostupna pres localhost na portu 5000
localhost:5000