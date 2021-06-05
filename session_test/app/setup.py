from configuraciones import *
import psycopg2
conn = psycopg2.connect("dbname=%s user=%s password=%s host=%s port=%s"%(db_database,db_user,db_passwd,db_host,db_port))


cur = conn.cursor()
sql ="""DROP SCHEMA public CASCADE;
CREATE SCHEMA public;"""

cur.execute(sql)

sql ="""
CREATE TABLE usuarios
           (id serial PRIMARY KEY, email varchar(100) unique, password varchar(255), nombre varchar(80), apellido varchar(80), tipo integer, nivel integer, fecha_registro timestamp);
"""

cur.execute(sql)

conn.commit()
cur.close()
conn.close()
