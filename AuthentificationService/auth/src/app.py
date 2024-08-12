import psycopg2
from flask import Flask, request, abort
from sqlalchemy import create_engine


app = Flask(__name__)

config = {
    'DATABASE_URI': 'postgresql+psycopg2://authuser:authpasswd@auth-postgresql:5432/authdb'
}

engine = create_engine(config['DATABASE_URI'], echo=True)

def get_db_connection():
    conn = psycopg2.connect(host='auth-postgresql',
                            database='authdb',
                            user='authuser',
                            password='authpasswd')
    return conn


SESSIONS = {}


def generate_session_id(size=40):
    import string
    import random
    chars = string.ascii_uppercase + string.digits + string.ascii_lowercase
    return ''.join(random.choice(chars) for _ in range(size))


def create_session(data):
    session_id = generate_session_id()
    SESSIONS[session_id] = data
    return session_id


def register_user(login, password, email, first_name, last_name):
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                insert into auth_user (login, password, email, first_name, last_name)
                values (%s, %s, %s, %s, %s) returning id;
                """, (login, password, email, first_name, last_name))
            conn.commit()
            id_ = cur.fetchall()
        return {"id": id_}
    except IntegrityError:
        abort(400, "login/email already exists")


def get_user_by_credentials(login, password):
    res = {}
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "select id, login, email, first_name, last_name from auth_user "
            "where login='{}' and password='{}'".format(login, password))
        user_id = cur.fetchall()
        res['id'] = user_id[0][0]
        res['login'] = user_id[0][1]
        res['email'] = user_id[0][2]
        res['first_name'] = user_id[0][3]
        res['last_name'] = user_id[0][4]
    return res


@app.route("/sessions", methods=["GET"])
def sessions():
    return SESSIONS


@app.route("/register", methods=["POST"])
def register():
    request_data = request.get_json()
    # add validation
    login = request_data['login']
    password = request_data['password']
    email = request_data['email']
    first_name = request_data['first_name']
    last_name = request_data['last_name']
    return register_user(login, password, email, first_name, last_name)


@app.route("/login", methods=["POST"])
def login():
    request_data = request.get_json()
    login = request_data['login']
    password = request_data['password']
    user_info = get_user_by_credentials(login, password)
    if user_info:
        session_id = create_session(user_info)
        response = app.make_response({"status": "ok"})
        response.set_cookie("session_id", session_id, httponly=True)
        return response
    else:
        abort(401)


@app.route("/signin", methods=["GET"])
def signin():
    return {"message": "Please go to login and provide Login/Password"}


@app.route('/auth')
def auth():
    if 'session_id' in request.cookies:
        session_id = request.cookies['session_id']
        if session_id in SESSIONS:
            data = SESSIONS[session_id]
            response = app.make_response(data)
            response.headers['X-UserId'] = data['id']
            response.headers['X-User'] = data['login']
            response.headers['X-Email'] = data['email']
            response.headers['X-First-Name'] = data['first_name']
            response.headers['X-Last-Name'] = data['last_name']
            return response
    abort(401)


@app.route("/logout", methods=["GET", "POST"])
def logout():
    response = app.make_response({"status": "ok"})
    response.set_cookie('session_id', '', expires=0)
    return response


@app.route("/health")
def health():
    return {"status": "OK"}


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80, debug=True)
