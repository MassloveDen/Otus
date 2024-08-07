from flask import Flask, request
import psycopg2
from metrics import register_metrics

app = Flask(__name__)

def get_db_connection():
    conn = psycopg2.connect(host='postgres',
                            database='postgres',
                            user='dbuser',
                            password='QWERTY')
    return conn

@app.route("/health")
def hello():
    return {"status": "OKEY"}

@app.route("/createDB")
def createDB():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DROP TABLE IF EXISTS users;')
    cur.execute('CREATE TABLE users (id serial PRIMARY KEY,'
                'username varchar (256) NOT NULL,'
                'firstName varchar (50) NOT NULL,'
                'lastName varchar (50) NOT NULL,'
                'email varchar (50) NOT NULL,'
                'phone varchar (50) NOT NULL);'
                )
    conn.commit()
    cur.close()
    conn.close()


@app.route('/user', methods=['POST'])
def create_user():
    body = request.get_json(silent=True)
    username = body['username']
    firstname = body['firstname']
    lastname = body['lastname']
    email = body['email']
    phone = body['phone']

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO users (username, firstname, lastname, email, phone) VALUES (%s, %s, %s, %s, %s)
        ''',
                (username, firstname, lastname, email, phone))

    conn.commit()
    cur.close()
    conn.close()
    return {"user created": "OK"}

@app.route('/user/<user_id>', methods=['GET', 'PUT', 'DELETE'])
def user(user_id):
    if request.method == 'GET':
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            '''
            SELECT * FROM users 
                WHERE id = %s
            ''',
            (user_id,))
        user_data = cur.fetchall()

        cur.close()
        conn.close()
        return user_data

    if request.method == 'PUT':
        body = request.get_json(silent=True)
        username = body['username']
        firstname = body['firstname']
        lastname = body['lastname']
        email = body['email']
        phone = body['phone']

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            '''update users 
            set username = %s, firstname = %s, lastname = %s, email = %s, phone = %s
            WHERE id = %s
            ''',
            (username, firstname, lastname, email, phone, user_id,))

        conn.commit()

        cur.close()
        conn.close()
        return {"user updated": "OK"}

    if request.method == 'DELETE':
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            '''
            DELETE FROM users 
                WHERE id = %s
            ''',
            (user_id,))
        conn.commit()

        cur.close()
        conn.close()
        return {"user deleted": "OK"}


@app.route('/metrics')
def metrics():
    from prometheus_client import generate_latest
    return generate_latest()

# run the application
if __name__ == "__main__":
    register_metrics(app)
    app.run(host='0.0.0.0', debug=True, port=8000)
