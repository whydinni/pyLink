from flask import Flask,request,redirect,jsonify, make_response
from flask_jwt_extended import create_access_token, JWTManager, get_jwt_identity, jwt_required
import sqlite3, uuid, hashlib, random
from werkzeug.security import generate_password_hash,check_password_hash

conn = sqlite3.connect('database.db', check_same_thread=False)
cursor = conn.cursor()
# cursor.execute('''CREATE TABLE "links" (
# 	"id"	INTEGER NOT NULL UNIQUE,
# 	"initialLink"	TEXT NOT NULL,
# 	"shortLink"	TEXT NOT NULL,
# 	"number"	INTEGER NOT NULL,
# 	PRIMARY KEY("id" AUTOINCREMENT)
# );''')
# cursor.execute('''CREATE TABLE "users" (
# 	"id"	INTEGER NOT NULL UNIQUE,
# 	"login"	TEXT NOT NULL UNIQUE,
# 	"password"	TEXT NOT NULL,
# 	PRIMARY KEY("id" AUTOINCREMENT)
# );''')
# cursor.execute('''CREATE TABLE "accessLink" (
# 	"id_user"	INTEGER NOT NULL,
# 	"id_link"	INTEGER NOT NULL,
# 	"access"	TEXT NOT NULL
# );''')


app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = "super-secret"
jwt = JWTManager(app)

@app.route('/')
def index():
    return "Hello World"

def convertList(link):
    str = ''
    for i in link:
        str += i+"\n"
    return str

@app.route('/register', methods = ["post"])
def reg():
    print('123')
    if request.method=='POST':
        print('5')
        login = str(request.json.get('login', None))
        password = str(request.json.get('password', None))
        return make_response(regis(cursor, conn, login, password))

@app.route('/autho', methods = ["post"])
def authorize():
    print('3')
    if request.method == 'POST':
        print('2')
        login = str(request.json.get('login', None))
        password = str(request.json.get('password', None))
        if auth(cursor, login, password):
            print('1')
            token=create_access_token(identity=login)
            return make_response(token)
        else:
            return make_response("error")



# @app.route('/link', methods = ["post", "get"])
# def links():
#     if request.method == 'POST':



def regis(cursor, connect, login, password):
    proverka = cursor.execute('SELECT login FROM users').fetchall()
    users=[]
    for item in proverka:
        users.append(item[0])
    if (login in users):
        return "Такой пользователь уже есть"
    else:
        cursor.execute('INSERT INTO users(login, password) VALUES(?, ?)',(login,password))
        connect.commit()
        return "Вы успешно зарегистрировались"

def auth(cursor, login, password):
    auth = cursor.execute('SELECT login, password FROM users').fetchall()
    users = dict()
    for item in auth:
        users[item[0]] = item[1]
    if (login in users.keys() and password == users.get(login)):
        return True
    else:
       return False

# def linkdb(cursos,)

if __name__ == "__main__":
        app.run()