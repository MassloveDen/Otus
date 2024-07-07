from flask import Flask, request
import psycopg2

app = Flask(__name__)


def get_db_connection():
    conn = psycopg2.connect(host='localhost',
                            database='postgresql',
                            user='DB_USERNAME',
                            password='DB_PASSWORD')
    return conn


@app.route("/health")
def hello():
    return {"status": "OK"}


@app.route('/user', methods=['POST'])
def create_user():
    username = request.args.get('username')
    first_name = request.args.get('first_name')
    last_name = request.args.get('last_name')
    email = request.args.get('email')
    phone = request.args.get('phone')

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO users (username, first_name, last_name, email, phone) VALUES (%s, %s, %s, %s, %s)
        ''',
                (username, first_name, last_name, email, phone))

    conn.commit()
    cur.close()
    conn.close()

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
        username = request.args.get('username')
        first_name = request.args.get('first_name')
        last_name = request.args.get('last_name')
        email = request.args.get('email')
        phone = request.args.get('phone')

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            '''update users 
            set username = %s, first_name = %s, last_name = %s, email = %s, phone = %s
            WHERE id = %s
            ''',
            (username, first_name, last_name, email, phone, user_id,))

        conn.commit()

        cur.close()
        conn.close()

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


# run the application
if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True, port=8000)
