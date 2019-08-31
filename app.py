from flask import Flask, session, g, redirect, url_for, escape, request, render_template
import sqlite3

from notification import send_push_message

from datetime import datetime

app = Flask(__name__)
app.secret_key = "/btPL/w79Wy21NYAkzXIa8U57Cc+z9DYRm8wH0OAwOxLJhJroaMFhF1i4K0Ng3Dk/IZOpo5j2IvsEbVw0vAegcdM4TtRGK9q6Ep8ow8jFyATacx1GgL9QKwlr83KSvgdMtH3Ecsvq+OKlPIvtoUvLAFWZedGqDXZ/ZrTMX70gaU="
# app.config.update(SERVER_NAME="0.0.0.0:80")

#52 0,12 * * * root certbot renew --renew-hook 'service nginx reload'

# start db ----------

DATABASE = 'database.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def insert_db(table, fields=(), values=()):
    # g.db is the database connection
    cur = get_db().cursor()
    query = 'REPLACE INTO %s (%s) VALUES (%s)' % (
        table,
        ', '.join(fields),
        ', '.join(['?'] * len(values))
    )
    cur.execute(query, values)
    get_db().commit()
    id = cur.lastrowid
    cur.close()
    return id

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

# end db ----------

@app.route("/")
def index():
    if 'logged_in' in session:
        return redirect(url_for('push'))
        
    return render_template('index.html')

@app.route("/push")
def push():
    if not 'logged_in' in session:
        return redirect(url_for('index'))
    return render_template('push.html')

@app.route("/login", methods=['POST', 'GET'])
def login():
    if request.method == 'GET':
        return redirect(url_for('index'))
    else:
        if request.form['password'] == "password":
            session['logged_in'] = True
            return redirect(url_for('push'))
        else:
            return render_template('index.html', error="Incorrect password. Please try again.")

@app.route("/logout")
def logout():
    del session['logged_in']
    return redirect(url_for('index'))

@app.route("/send_notification", methods=['POST'])
def send_notification():
    # send_push_message("ExponentPushToken[Yw7Cd2MCoI8gVW-BJEEOs-]", "This is a test", None)
    # send_push_message("ExponentPushToken[0vWyuUGUjqenh4J7_OI1oe]", "This is a test", None)
    n = 0
    for user in query_db("select * from users", []):
        n += 1
        send_push_message(user['push_token'], "Don't forget to come to the meeting at lunch today! " + user['device_id'], None)
    return "Success " + str(n)


@app.route("/register", methods=['POST'])
def register():
    content = request.json
    token = content['token']['value']
    device = content['user']['deviceId']

    res = insert_db('users', ['push_token', 'device_id'], [token, device])
    print(res)
    return 'Success ' + str(res)

@app.route("/update", methods=['POST'])
def update():
    content = request.json
    print(content)
    device_id = str(content['deviceId'])
    push_token = str(content['pushToken'])
    name = str(content['name'])
    grade = int(content['grade'])
    gender = str(content['gender'])
    email = str(content['email'])
    pemail = str(content['pemail'])
    phone = str(content['phone'])

    device_name = str(content['deviceName'])
    device_year = str(content['deviceYear'])
    platform = str(content['platform'])
    ownership = str(content['ownership'])
    last_modified = datetime.now().strftime('%Y-%m-%d')

    insert_db(
        'users',
        ['device_id', 'push_token', 'name', 'grade', 'gender', 'email', 'pemail', 'phone', 'device_name', 'device_year', 'platform', 'ownership', 'last_modified'],
        [device_id, push_token, name, grade, gender, email, pemail, phone, device_name, device_year, platform, ownership, last_modified]
    )


    