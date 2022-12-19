from flask import Flask, request, redirect, jsonify, make_response
from flask_jwt_extended import create_access_token, JWTManager, get_jwt_identity, jwt_required
import sqlite3, uuid, hashlib, random
from werkzeug.security import generate_password_hash, check_password_hash

conn = sqlite3.connect('database.db', check_same_thread=False)
cursor = conn.cursor()
# cursor.execute('''CREATE TABLE "links" (
#     "id" INTEGER NOT NULL,
#     "login" TEXT NOT NULL,
#     "link" TEXT NOT NULL,
#     "shortlink" TEXT NOT NULL,
#     "access" TEXT NOT NULL,
#     "count"	INTEGER NOT NULL,
#     PRIMARY KEY("id" AUTOINCREMENT)
# );''')
# cursor.execute('''CREATE TABLE "users" (
# 	"id"	INTEGER NOT NULL UNIQUE,
# 	"login"	TEXT NOT NULL UNIQUE,
# 	"password"	TEXT NOT NULL,
# 	PRIMARY KEY("id" AUTOINCREMENT)
# );''')

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = "super-secret"
jwt = JWTManager(app)

def convertList(link):
    str = ''
    for i in link:
        str += i+"\n"
    return str

#----------------------------------------------------------------------------------------
#ОСНОВНЫЕ ФУНКЦИИ
#----------------------------------------------------------------------------------------

# регистрация пользователя
@app.route('/register', methods = ["post"])
def reg():
    if request.method=='POST':
        login = str(request.json.get('login', None))
        password = str(request.json.get('password', None))
        return make_response(regis(cursor, conn, login, password))

# авторизация пользователя
@app.route('/autho', methods = ["post"])
def authorize():
    if request.method == 'POST':
        login = str(request.json.get('login', None))
        password = str(request.json.get('password', None))
        user = users(cursor, conn, login)
        if user!=None:
            return make_response(auth(cursor, conn, user, login, password))
        else:
            return make_response("Где то ошибка, проверьте введенные данные.")

# добавление ссылки
@app.route("/add_link", methods=['POST'])
@jwt_required()
def add_link():
    login = str(get_jwt_identity())
    link = str(request.json.get("link", None))
    shortlink = str(request.json.get("shortlink", None))
    if shortlink == "":
        shortlink = str(hashlib.md5(link.encode()).hexdigest()[:random.randint(8, 12)])
    count = 0
    access = 'public'
    add(cursor, conn, login, link, shortlink, access, count)
    return make_response(f'Вы успешно добавили ссылку. Ваша короткая ссылка - {shortlink}')

#просмотр сокращенных ссылок активного пользователя
@app.route("/myLinks", methods=['POST'])
@jwt_required()
def myLinks():
    login = str(get_jwt_identity())
    links = allLinks(cursor, conn, login)
    my_links = ''.join(map(str, links))
    if links != []:
        return make_response(f"Все ваши сокращенные ссылки: \n {my_links}")
    else:
        return make_response("У вас нет сокращенных ссылок :(")

#смена вида доступа
@app.route("/change", methods=['POST'])
@jwt_required()
def accessChange():
    login = str(get_jwt_identity())
    shortlink = str(request.json.get("shortlink", None))
    access = str(request.json.get("access", None))
    change(cursor, conn, shortlink, access, login)
    return make_response('Вы поменяли вид доступа')

#удаление ссылки
@app.route("/delete", methods=['POST'])
@jwt_required()
def delete():
    login = str(get_jwt_identity())
    shortlink = str(request.json.get("shortlink", None))
    deleteLink(cursor, conn, shortlink, login)
    return make_response('Вы удалили ссылку :( ')

#изменение сокращенной ссылки
@app.route("/changeName", methods=['POST'])
@jwt_required()
def changeName():
    login = str(get_jwt_identity())
    old = str(request.json.get("old", None))
    new = str(request.json.get("new", None))
    changeNikname(cursor, conn, old, new, login)
    return make_response('Вы поменяли сокращенную ссылку')

#просмотр публичных ссылок
@app.route("/public", methods=['POST'])
def publics():
    shortlink = str(request.json.get("shortlink", None))
    link = getLink(cursor, conn, shortlink)
    if link != None and link[4] == 'public':
        return view(shortlink)
    else:
        return make_response("Кажется, такой ссылки нет или у вас нет доступа к ней")

#просмотр приватных ссылок
@app.route("/private", methods=['POST'])
@jwt_required()
def privates():
    login = str(get_jwt_identity())
    user = users(cursor, conn, login)
    shortlink = str(request.json.get("shortlink", None))
    link = getLink(cursor, conn, shortlink)
    if user[1] == link[1] and link[4] == 'private':
        print(link[3])
        return view(shortlink)
    else:
        return make_response("Кажется, такой ссылки нет или она не ваша")

#просмотр количества переходов по ссылке
@app.route("/clicks", methods=['POST'])
def count():
    shortlink = str(request.json.get("shortlink", None))
    ct = cont(cursor, conn, shortlink)
    count = ''.join(map(str, ct))
    return make_response(f"Количество переходов по ссылке {shortlink} - {count[1]}")

#----------------------------------------------------------------------------------------
#ФУНКЦИИ ДЛЯ ОСНОВНЫХ ФУНКЦИЙ
#----------------------------------------------------------------------------------------

# проверка пользователя при регистрации
def regis(cursor, connect, login, password):
    proverka = cursor.execute('SELECT login FROM users').fetchall()
    users=[]
    for item in proverka:
        users.append(item[0])
    if (login in users):
        return "Такой пользователь уже есть"
    else:
        cursor.execute('INSERT INTO users(login, password) VALUES(?, ?)',(login, generate_password_hash(password)))
        connect.commit()
        return "Вы успешно зарегистрировались :)"

# проверка пользователя при авторизации
def auth(cursor, conn, user, login, password):
    if check_password_hash(user[2], password):
        token = create_access_token(identity=login)
        return make_response(f" Вы авторизовались. Ваш токен - {token}")
    else:
        return make_response("Где-то ошибка, проверьте введенные данные.")

#для добавления ссылки
def add(cursor, conn, login, link, shortlink, access, count) :
    sql = "INSERT INTO links (login, link, shortlink, access, count) VALUES (:login, :link, :shortlink, :access, :count)"
    cursor.execute(sql, {'login': login, 'link': link, 'shortlink': shortlink, 'access': access, 'count': count})
    conn.commit()

#получение короткой ссылки
def getLink (cursor, conn, shortlink) :
    result = cursor.execute("SELECT links.* FROM links WHERE shortlink=:shortlink", {'shortlink': shortlink}).fetchone()
    conn.commit()
    return result

#просмотр ссылки
@app.route("/<short>", methods=['POST'])
def view(short):
    link = getLink(cursor, conn, short)
    count = link[5]
    clicks(cursor, conn, short, count)
    return redirect(link[2])

# подсчет переходов по ссылке
def clicks (cursor, conn, shortlink, count) :
    result = cursor.execute('''UPDATE links SET count=? WHERE shortlink=?''', (count + 1, shortlink,))
    conn.commit()
    return result

#для вывода количества переходов по ссылке
def cont(cursor, conn, shortlink):
    sql = "SELECT count FROM links WHERE shortlink= :shortlink"
    result = cursor.execute(sql, {'shortlink': shortlink}).fetchall()
    conn.commit()
    return result

# ссылки пользователя
def allLinks (cursor, conn, login) :
    sql = "SELECT links.shortlink FROM links WHERE login= :login"
    result = cursor.execute(sql, {'login': login}).fetchall()
    conn.commit()
    return result

#проверка пользователя для ссылок
def users (cursor, connect, login) :
    sql = "SELECT users.* FROM users WHERE login= :login"
    result = cursor.execute(sql, {'login': login}).fetchone()
    connect.commit()
    return result

#для изменения вида доступа
def change (cursor, conn, shortlink, access, login) :
    sql = "UPDATE links SET access=:access WHERE shortlink=:shortlink AND login=:login"
    cursor.execute(sql, {'shortlink': shortlink, 'access': access, 'login': login})
    conn.commit()

#для удаления ссылки
def deleteLink (cursor, conn, shortlink, login) :
    sql = "DELETE FROM links WHERE login=:login AND shortlink=:shortlink"
    cursor.execute(sql, {'shortlink': shortlink, 'login': login})
    conn.commit()

#для изменения сокращенной ссылки
def changeNikname (cursor, conn, old, new, login) :
    sql = "UPDATE links SET shortlink=:new WHERE shortlink=:old AND login=:login"
    cursor.execute(sql, {'old': old, 'new': new, 'login': login})
    conn.commit()

if __name__ == "__main__":
        app.run()
