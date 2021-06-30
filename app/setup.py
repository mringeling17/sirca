from configuraciones import *
import psycopg2
conn = psycopg2.connect("dbname=%s user=%s password=%s host=%s port=%s"%(db_database,db_user,db_passwd,db_host,db_port))


cur = conn.cursor()
sql ="""DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
CREATE EXTENSION pgcrypto;
"""

cur.execute(sql)

sql ="""
CREATE TABLE usuarios
           (id serial PRIMARY KEY, email varchar(100) unique, password varchar(255), nombre varchar(80), apellido varchar(80), tipo integer, nivel integer, fecha_registro timestamp);
"""

cur.execute(sql)

sql ="""
insert into usuarios (email,password,nombre,apellido,tipo,nivel,fecha_registro) values ('admin@cuy.cl',crypt('admin', gen_salt('bf')),'Super','Administrador',2,0,now());
"""

cur.execute(sql)

sql = """
CREATE TABLE reservas
            (id serial PRIMARY KEY, disponible bool, fecha date, bloque integer, jugador1 integer, jugador2 integer, invitado1 varchar(160), invitado2 varchar(160), cancha integer, tx1 integer, tx2 integer, tipo_reserva integer, pago integer, fecha_reserva timestamp);
"""

cur.execute(sql)

sql = """
CREATE TABLE transacciones
            (id serial PRIMARY KEY, id_usuario integer, url varchar(255), fecha timestamp)
"""

cur.execute(sql)

sql = "CREATE TABLE token (email varchar(100), token_id varchar(50), used boolean)"
cur.execute(sql)


conn.commit()
cur.close()
conn.close()
