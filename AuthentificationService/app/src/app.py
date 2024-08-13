import psycopg2
from flask import Flask, request


app = Flask(__name__)

config = {
    'DATABASE_URI': 'postgresql+psycopg2://appuser:apppasswd@app-postgresql:5432/appdb'
}


def get_db_connection():
    conn = psycopg2.connect(host='app-postgresql',
                            database='appdb',
                            user='appuser',
                            password='apppasswd')
    return conn


@app.route('/vers')
def vers():
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("select version()")
        result = cur.fetchone()
    return {"res": result}


@app.route('/users/me')
def me():
    if 'X-UserId' not in request.headers:
        return "Not authenticated"
    data = {}
    data['id'] = request.headers['X-UserId']
    data['login'] = request.headers['X-User']
    data['email'] = request.headers['X-Email']
    data['first_name'] = request.headers['X-First-Name']
    data['last_name'] = request.headers['X-Last-Name']

    rows = []
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "select avatar_uri, age from user_profile "
            "where id={} limit 1".format(data['id']))
        result = cur.fetchone()
    if rows:
        data['avatar_url'] = result[0][0]
        data['age'] = result[0][1]
    return data


@app.route("/users/me", methods=["PUT"])
def updateMe():
    if 'X-UserId' not in request.headers:
        return "Not authenticated"
    request_data = request.get_json()
    id = request.headers['X-UserId']
    avatar_uri = request_data['avatar_uri']
    age = request_data['age']
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            insert into user_profile (id, avatar_uri, age)
            values ('{}', '{}', {})
            on conflict (id)
            do update set
                avatar_uri = excluded.avatar_uri, age = excluded.age;
            """.format(id, avatar_uri, age))
    data = {}
    data['id'] = id
    data['avatar_uri'] = avatar_uri
    data['age'] = age

    return data


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80, debug=True)
