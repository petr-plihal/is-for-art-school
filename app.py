from flask import Flask, render_template, redirect
import pymysql
from model import db, insert_data, delete_one

pymysql.install_as_MySQLdb()

# Vytvoreni flask aplikace
app = Flask(__name__)

# Pripojeni k databazi lokalni MySQL/google cloud
#app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://sammy:password@localhost/demo'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://artist:&.{lE0A1i2&G$t3j@35.187.170.251/umelecka_skola'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Routes pro jednotlive stranky databaze
# Nacte pocatecni stranku s tlacitky
@app.route('/')
def index():
    return render_template('database.html')

# Vytvori databazi
@app.route('/db')
def create_db():    
    with app.app_context():
        db.create_all()
    print("Database connection successful!")
    return redirect('/')

# Zruseni vsech tabulek v databazi
@app.route('/dropdb')
def drop_db():
    db.drop_all()
    print("Database tables dropped!")
    return redirect('/')

# Naplneni databaze daty
@app.route('/insert')
def insert():
    insert_data()
    #delete_one()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)