from app import app
from flask import render_template,request,redirect,session, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import date, timedelta
from app import configuraciones
from flask_mail import Mail

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
	if request.method == 'POST':
		idrec = int(request.form.get("idreserva",""))
		sql = """SELECT disponible,tipo_reserva from reservas where id = %s"""%(idrec)
		cur.execute(sql)
		tiporeserva = cur.fetchone()
		disponibilidad = tiporeserva[0]
		tiporeserva1 = tiporeserva[1]#tenemos el numero para saber si es parcial o no
		if disponibilidad == True: #esta vacia(disponible totalmente)
			if not 'username' in session: #si no es usuario
				return redirect("/login")
			else:
				if session['tipo']!=2: #si es usuario normal
					sql = """SELECT nombre, apellido, nivel FROM usuarios WHERE id = %s;"""%(session['user_id'])
					cur.execute(sql)
					datosusuario = cur.fetchall()
					nombre = datosusuario[0][0]
					apellido = datosusuario[0][1]
					nivelint = int(datosusuario[0][2])
					email = session['username']
					if nivelint == 1:
						nivelfinal = "Nivel básico"
					elif nivelint == 2:
						nivelfinal = "Nivel Intermedio"
					else:
						nivelfinal = "Nivel Alto"
					return render_template("datosuser.html",idrec=idrec,nombre=nombre,apellido=apellido,email=email,nivelfinal=nivelfinal)#se autocompleta
				else: #si es admin
					return render_template("datosres.html",idrec=idrec) #para completar
		else: #ya tiene una parcial
			if not 'username' in session: #si no es usuario
				return redirect("/login")
			else:
				if session['tipo'] != 2: #usuario normal
					sql = """SELECT jugador1 FROM reservas WHERE id = %s"""%(idrec)#id del jugador que tiene la reserva parcial
					cur.execute(sql)
					idjugador1 = cur.fetchone()
					idjugador = idjugador1[0]
					sql = """SELECT nombre,apellido,nivel FROM usuarios WHERE id = %s;"""%(idjugador)#datos del jugador con la reserva parcial
					cur.execute(sql)
					datosusuario = cur.fetchall()
					nombre = datosusuario[0][0]
					apellido = datosusuario[0][1]
					nivelint = int(datosusuario[0][2])
					if nivelint == 1:
						nivelfinal = "Nivel básico"
					elif nivelint == 2:
						nivelfinal = "Nivel Intermedio"
					else:
						nivelfinal = "Nivel Alto"
					sql = """SELECT nombre, apellido FROM usuarios WHERE id = %s;"""%(session['user_id'])
					cur.execute(sql)
					datosusuario = cur.fetchall()
					nombreses = datosusuario[0][0]
					apellidoses = datosusuario[0][1]
					emailses = session['username']
					return render_template("datosuser_p.html",idrec=idrec,nombre = nombre,apellido=apellido,nivelfinal=nivelfinal,nombreses=nombreses,apellidoses=apellidoses,emailses=emailses)
				else: #admin realiza reserva parcial
					sql = """SELECT jugador1 FROM reservas WHERE id = %s"""%(idrec)#id del jugador que tiene la reserva parcial
					cur.execute(sql)
					idjugador1 = cur.fetchone()
					idjugador = idjugador1[0]
					sql = """SELECT nombre,apellido,nivel FROM usuarios WHERE id = %s;"""%(idjugador)#datos del jugador con la reserva parcial
					cur.execute(sql)
					datosusuario = cur.fetchall()
					nombre = datosusuario[0][0]
					apellido = datosusuario[0][1]
					nivelint = int(datosusuario[0][2])
					if nivelint == 1:
						nivelfinal = "Nivel básico"
					elif nivelint == 2:
						nivelfinal = "Nivel Intermedio"
					else:
						nivelfinal = "Nivel Alto"
					return render_template("datosres_p.html",idrec=idrec,nombre=nombre,apellido=apellido,nivelfinal=nivelfinal)

@app.route('/realizar_reserva', methods = ['POST','GET']) #completar la reserva y gurdarla en la base
def realizar_reserva():
	if request.method == 'POST':
		if not 'username' in session: #si no es usuario
			return redirect("/login")
		else:
			if session['tipo']!=2: #si es usuario normal
				idrec = int(request.form.get("idreserva",""))
				idusuario = int(session['user_id'])
				pago = request.form['opcionespag']
				tipo = int(request.form.get("tipo_reserva"))
				if tipo == 1: #reserva parcial, falta ver lo del pago
					sql = """UPDATE reservas SET disponible = False, jugador1 = %s , tipo_reserva = 1 WHERE id = %s"""%(idusuario,idrec)
					cur.execute(sql)
					cur.commit() #reserva parcial jugador registrado
					return render_template("") #falta html para confirmar que se hizo la reserva
				else: #reserva completa
					sql = """UPDATE reservas SET disponible = False, jugador1 = %s, tipo_reserva = 2 WHERE id = %s"""%(idusuario,idrec)
					cur.execute(sql)
					cur.commit() #reserva completa jugador registrado
					return render_template("") #falta html para confirmar que se hizo la reserva
			else: #admin, reserva completa
				idrec = int(request.form.get("idreserva",""))
				nombre = request.form['nombrer']
				apellido = request.form['apellr']
				invitado1 = nombre + " " + apellido
				sql = """UPDATE reservas SET disponible = False, invitado1 = %s,tipo_reserva = 2,pago = 3 WHERE id = %s"""%(invitado1,idrec)
				cur.execute(sql)
				cur.commit() #reserva completa invitado1
				return render_template("") #falta html para confirmar que se hizo la reserva

@app.route('/realizar_reserva_parcial', methods = ['POST','GET']) #completar la reserva parcial y guardarla en la base
def realizar_reserva_parcial():
	if request.method == 'POST':
		if not 'username' in session: #si no es usuario
			return redirect("/login")
		else:
			if session['tipo']!=2: #si es usuario normal
				idrec = int(request.form.get("idreserva",""))
				jugador2 = int(session['user_id']) #falta setear lo del pago
				sql = """UPDATE reservas SET jugador2 = %s,tipo_reserva = 2 WHERE id = %s"""%(jugador2,idrec)
				cur.execute(sql)
				cur.commit() #completar reserva parcial con otro jugador registrado, registrado/registrado
				return render_template("") #falta html para confirmar que se hizo la reserva
			else: #admin
				idrec = int(request.form.get("idreserva",""))
				nombre = request.form['nombrer']
				apellido = request.form['apellr']
				invitado1 = nombre + " " + apellido  #falta setear lo del pago
				sql = """UPDATE reservas SET invitado1 = %s,tipo_reserva = 2 WHERE id = %s"""(invitado1,idrec)
				cur.execute(sql)
				cur.commit() #completar reserva parcial con un invitado, registrado/invitado
				return render_template("") #falta html para confirmar que se hizo la reserva




@app.route("/confirmation")
def confirmation():
	app.config['MAIL_SERVER'] = 'sirca.cuy.cl'
	app.config['MAIL_PORT'] = 465
	app.config['MAIL_USERNAME'] = 'sirca@cuy.cl'
	app.config['EMAIL_PASSWORD'] = 'OXurpKj708'
	app.config['MAIL_USE_TLS'] = False
	app.config['MAIL_USE_SSL'] = True
	mail = Mail(app)

	#sql1 = "select nombre from Usuarios where id = id_jugador_loggeado"
	#sql2 = "select correo from Usuarios where id = id_jugador_loggeado"
	#cur.execute(sql1)
	#nombre = cur.fetchall()
	#cur.execute(sql2)
	#correo = cur.fetchall()
    msg = Message('Hola, ', sender='sirca@cuy.cl', recipients='correo@dominio.cl')
    msg.body = "Reserva creada exitosamente"
    mail.send(msg)
    return "Enviado"


@app.route('/reset/<token>', methods = ["GET", "POST"])
def reset_with_token(token):
    try:
        email = ts.loads(token, salt="recover-key", max_age = 86400)
    except:
        abort(404)

    form = PasswordForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=email).first_or_404()

        user.password = form.password.data

        db.session.add(user)
        db.session.commit()

        return redirect(url_for('/signin'))
    return render_template('reset_with_token.html', form = form, token = token)
