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
            "select balance from user_profile "
            "where id={} limit 1".format(data['id']))
        result = cur.fetchone()
    if rows:
        data['balance'] = result[0][0]
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


@app.route("/updateBalance", methods=["PUT"])
def update_balance():
    if 'X-UserId' not in request.headers:
        return "Not authenticated"
    request_data = request.get_json()
    id = request.headers['X-UserId']
    balance = request_data['balance']
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            update user_profile (balance)
            values ('{}')
            on conflict (id)
            do update set
                balance = balance + excluded.balance;
            """.format(id, balance))
    data = {'id': id, 'balance': balance}

    return data


@app.route("/products", methods=["GET"])
def get_products():
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "select * from products"
        )

        result = cur.fetchone()
    return {"products": result}


@app.route("/products/<product_id>", methods=['POST', 'DELETE'])
def add_product(product_id):
    if 'X-UserId' not in request.headers:
        return "Not authenticated"
    user_id = request.headers['X-UserId']
    if request.method == 'POST':
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "insert into orders (product_id, user_id, price) "
                "values ({}, {}, (select cost from products where id = product_id))"
                .format(product_id, user_id)
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
    user_id = request.headers['X-UserId']
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "select * from orders "
            "where user_id='{}' ".format(user_id)
        )
        result = cur.fetchone()
        total_cost = sum(result['cost'])
    return {f"Стоимость заказа равна {total_cost} руб."}


@app.route("/orderPurchase", methods=["POST"])
def order_purchase():
    user_id = request.headers['X-UserId']
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "select * from orders "
            "where user_id='{}' ".format(user_id)
        )
        result = cur.fetchone()
        total_cost = sum(result['cost'])
        cur.execute(
            "select balance from user_profile "
            "where user_id='{}' ".format(user_id)
        )
        user_balance = cur.fetchone()
        balance = user_balance[0]
        if balance < total_cost:
            return {"На Вашем счете недостаточно средств. Пополните счет или измените заказ"}
        else:
            cur.execute(
                "delete from orders "
                "where user_id='{}' ".format(user_id)
            )
            cur.execute(
                "update user_profile "
                "set balance = balance - total_cost "
                "where user_id='{}' ".format(user_id)
            )
            return {"ok": "Покупка совершена"}


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80, debug=True)
