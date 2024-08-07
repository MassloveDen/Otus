import psycopg2

conn = psycopg2.connect(
    host="postgres",
    database="postgres",
    user="dbuser",
    password="QWERTY")

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
