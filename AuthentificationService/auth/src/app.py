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
    except Exception as e:
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


@app.route("/updateBalance", methods=["PUT"])
def update_balance():
    # if 'X-UserId' not in request.headers:
    #     return "Not authenticated"
    request_data = request.get_json()
    # id = request.headers['X-UserId']
    balance = request_data['balance']
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            update auth_user 
            set balance = balance + '{}' where id = 30 returning balance;
            """.format(balance))
        balance = cur.fetchall()

    return {"Ваш текущий баланс": balance}


@app.route("/products", methods=["GET"])
def get_products():
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """select * from products"""
        )

        result = cur.fetchall()
    return {"products": result}

# @app.route("/products/<product_id>", methods=["GET"])
# def get_product_info(product_id):
#     with get_db_connection() as conn:
#         cur = conn.cursor()
#         cur.execute(
#             """select * from products
#             where id = '{}'""".format(product_id)
#         )
#
#         result = cur.fetchall()
#     return {"products": result}

@app.route("/drop", methods=["GET"])
def del_table():
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            update auth_user 
            set balance = 0 
            where id = 30;
            """
        )
        # result = cur.fetchall()
    return {"result": "ok"}


@app.route("/users", methods=["GET"])
def get_users():
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            select * from auth_user; 
            """
        )

        result = cur.fetchall()
    return {"products": result}


@app.route("/products/<product_id>", methods=['POST', 'DELETE'])
def add_product(product_id):
    # if 'X-UserId' not in request.headers:
    #     return "Not authenticated"
    # user_id = request.headers['X-UserId']
    user_id = 30
    if request.method == 'POST':
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "insert into orders (product_id, user_id, price) "
                "values ({}, {}, (select cost from products where id = '{}'))"
                "returning id"
                .format(product_id, user_id, product_id)
            )
            result = cur.fetchone()
        return {"orders": result}
    if request.method == 'DELETE':
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "DELETE FROM orders WHERE product_id = {} AND user_id = {}"
                .format(product_id, user_id))
        return {"ok": "order deleted"}


@app.route("/orders", methods=["GET"])
def get_orders():
    # user_id = request.headers['X-UserId']
    user_id = 30
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "select price from orders "
            "where user_id='{}' ".format(user_id)
        )
        result = cur.fetchall()
    total_cost = sum(i[0] for i in result)
    return {"Стоимость заказа в руб.": total_cost}


@app.route("/orderPurchase", methods=["POST"])
def order_purchase():
    # user_id = request.headers['X-UserId']
    user_id = 30
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "select * from orders "
            "where user_id='{}' ".format(user_id)
        )
        result = cur.fetchall()
        total_cost = sum(i[0] for i in result)
        cur.execute(
            "select balance from auth_user "
            "where id='{}' ".format(user_id)
        )
        user_balance = cur.fetchone()
        balance = user_balance[0]
        if balance < total_cost:
            return {"Error": "На Вашем счете недостаточно средств. Пополните счет или измените заказ"}
        else:
            cur.execute(
                "delete from orders "
                "where user_id='{}' ".format(user_id)
            )
            cur.execute(
                "update auth_user "
                "set balance = balance - '{}' "
                "where id='{}' ".format(user_id, total_cost)
            )
            return {"ok": "Покупка совершена"}


@app.route("/health", methods=["GET"])
def health():
    return {"status": "OK"}


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80, debug=True)
