# IIS_projekt
IIS Projekt - Umělecká škola

# Prvni spusteni
### Stazeni a spusteni virtual env
`pip3 install virtualenv`
`virtualenv env`
`source env/bin/activate`

### Pridani balicku do virtualenv
`pip3 install flask flask-sqlalchemy pymysql flask-bycrypt flask-login`

### Samotne spusteni aplikace
`python3 app.py`
### Aplikace je pak dostupna pres localhost na portu 5000
`localhost:5000`

#### Pouzivani databaze
Pri pouzivani googlecloud databaze by to melo bezet bez problemu, ale pokud budete chtit pouzivat lokalni mySQL server, je potreba:
- stahnout mySQL
- vytvorit databazi
- vytvorit uzivatele a predat mu prava


#### Ukazkový uživatelé
##### Loginy
Správci: spravce1
Učitele: vyucuj1, vyucuj2
Uživatele: user1, user2, user3
##### Heslo pro všechny
aaa