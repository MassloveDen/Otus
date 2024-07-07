import os
import psycopg2

conn = psycopg2.connect(
    host="localhost",
    database="flask_db",
    user=os.environ['DB_USERNAME'],
    password=os.environ['DB_PASSWORD'])

cur = conn.cursor()
cur.execute('DROP TABLE IF EXISTS users;')
cur.execute('CREATE TABLE users (id serial PRIMARY KEY,'
            'username varchar (256) NOT NULL,'
            'firstName varchar (50) NOT NULL,'
            'lastName varchar (50) NOT NULL,'
            'email varchar (50) NOT NULL,'
            'phone varchar (50) NOT NULL,);'
            )

conn.commit()

cur.close()
conn.close()
