from app import app
from flask import render_template,request,redirect,session, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import date, timedelta
from app import configuraciones


conn = psycopg2.connect("dbname=%s user=%s password=%s host=%s port=%s"%(configuraciones.db_database,configuraciones.db_user,configuraciones.db_passwd,configuraciones.db_host,configuraciones.db_port))
conn.autocommit = True
#cur = conn.cursor()
cur = conn.cursor(cursor_factory=RealDictCursor)

app.secret_key = configuraciones.session_key

@app.route('/')
def home():
	if not 'username' in session:
		return redirect("/login")
	else:
		if session['tipo']==2:
			return redirect("/admin")
		else:
			return render_template("home.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		sql = """select id,email,tipo from usuarios where email = '%s' and password = crypt('%s', password);"""%(request.form['email'],request.form['password'])
		cur.execute(sql)
		print(sql)
		array = cur.fetchone()
		print(array)
		if array:
			session['username']=array['email']
			session['user_id']=array['id']
			session['tipo']=array['tipo']
			return redirect("/")
		else:
			return redirect("/login?error=1")
	return render_template("login.html")

@app.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
	if request.method == 'POST':
		sql = """insert into usuarios (email,password,nombre,apellido,tipo,nivel,fecha_registro) values ('%s',crypt('%s', gen_salt('bf')),'%s','%s',1,%s,now());"""%(request.form['email'],request.form['password'],request.form['nombre'],request.form['apellido'],request.form['nivel'])
		
		cur.execute(sql)
		conn.commit()
		return redirect("/login")
	return render_template("sign_up.html")


@app.route('/logout')
def logout():
	session.pop('username', None)
	session.pop('user_id', None)
	session.pop('tipo', None)
	return redirect("/login")

@app.route('/admin')
def admin():
	if not 'username' in session:
		return redirect("/login")
	else:
		if session['tipo']!=2:
			return redirect("/")
		else:
			return "<h1>Eres admin!!!</h1>"

@app.route('/init_day/<date>/', methods=['GET'])
def init_day(date):
	if not 'username' in session:
		output = {"status": "-1", "msg": "No logged in"}
		return jsonify(output)
	else:
		if session['tipo']!=2:
			output = {"status": "-1", "msg": "Not admin"}
			return jsonify(output)
		else:
			sql = """delete from reservas where fecha = '%s'"""%(date)
			cur.execute(sql)
			for i in range(1,7):
				cancha = 1
				sql = """insert into reservas (disponible,fecha,bloque,cancha) values (true,'%s',%s,%s);"""%(date,i,cancha)
				cur.execute(sql)
			for i in range(1,7):
				cancha = 2
				sql = """insert into reservas (disponible,fecha,bloque,cancha) values (true,'%s',%s,%s);"""%(date,i,cancha)
				cur.execute(sql)
			output = {"status": "1", "msg": "Executed"}
			return jsonify(output)

@app.route('/get_disp/<date>', methods=['GET'])
def get_disp(date):
	if not 'username' in session:
		output = {"status": "-1", "msg": "No logged in"}
		return jsonify(output)
	else:
		sql = """select id, cancha, bloque, disponible, tipo_reserva from reservas where fecha = '%s' and cancha = %s;"""%(date,1)
		cur.execute(sql)
		array1 = cur.fetchall()
		sql = """select id, cancha, bloque, disponible, tipo_reserva from reservas where fecha = '%s' and cancha = %s;"""%(date,2)
		cur.execute(sql)
		array2 = cur.fetchall()
		json_array = []
		json_array.append(array1)
		json_array.append(array2)
		return jsonify(json_array)

@app.route('/disponibilidad', methods = ['POST','GET'])
def disponibilidad():

	# Arreglo de los próximos 7 días
	dias = [date.today().strftime("%Y-%m-%d"),(date.today() + timedelta(days=1)).strftime("%Y-%m-%d"),(date.today() + timedelta(days=2)).strftime("%Y-%m-%d"),(date.today() + timedelta(days=3)).strftime("%Y-%m-%d"),(date.today() + timedelta(days=4)).strftime("%Y-%m-%d"),(date.today() + timedelta(days=5)).strftime("%Y-%m-%d"),(date.today() + timedelta(days=6)).strftime("%Y-%m-%d")]

	if request.method == 'POST':
		dia_id = int(request.form['dia'])
		fecha = dias[int(request.form['dia'])-1]
	else:
		dia_id = 1
		fecha = dias[0]

	sql = """select id, cancha, bloque, disponible, tipo_reserva from reservas where fecha = '%s' and cancha = %s;"""%(fecha,1)
	cur.execute(sql)
	cancha1 = cur.fetchall()
	sql = """select id, cancha, bloque, disponible, tipo_reserva from reservas where fecha = '%s' and cancha = %s;"""%(fecha,2)
	cur.execute(sql)
	cancha2 = cur.fetchall()

	return render_template("tabla_reserva.html", dia_id=dia_id, dias=dias,cancha1=cancha1, cancha2=cancha2)
	

@app.route('/add_reserva', methods = ['POST','GET'])
def add_reserva():
	return "Hay que implementarlo :("