from os import abort
import re
from app import app
from flask import render_template,request,redirect,session, jsonify, url_for, flash
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import date, datetime, timedelta
from app import configuraciones
from flask_mail import Mail, Message
from .__init__ import mail
from .keygen import generator
from app import keygen
from .flow import *
import secrets

sirca_url = "https://sirca.cuy.cl"

conn = psycopg2.connect("dbname='%s' user='%s' password='%s' host='%s' port='%s'"%(configuraciones.db_database,configuraciones.db_user,configuraciones.db_passwd,configuraciones.db_host,configuraciones.db_port))
conn.autocommit = True
#cur = conn.cursor()
cur = conn.cursor(cursor_factory=RealDictCursor)
cur2 = conn.cursor()

app.secret_key = configuraciones.session_key

@app.route('/')
def home():
	if not 'username' in session:
		return redirect("/login")
	else:
		if session['tipo']==2:
			return redirect("/admin")
		else:
			user = session['username']
			sql1 = """select id from usuarios where email = '%s'"""%(user)
			cur2.execute(sql1)
			id = cur2.fetchone()
			print(id)
			print(id[0])
			sql = """select fecha, bloque, cancha from reservas where jugador1 = '%s' or jugador2 = '%s' order by fecha desc, bloque asc """%(id[0],id[0])
			cur2.execute(sql)
			data = cur2.fetchall()
			print(data[0][0])
			print(data[0][1])
			print(data[0][2])

			return render_template('home.html',data = data)

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
			flash('Sesion Iniciada Correctamente',category='success')
			return redirect("/")
		else:
			flash('Los datos ingresados no son correctos', category='error')
			return redirect("/login?error=1")
	return render_template("login.html")

@app.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
	if request.method == 'POST':
		email = request.form['email']
		sql = """select count(*) from usuarios where email = '%s'"""%(email)
		cur2.execute(sql)
		count = cur2.fetchone()
		print(count)
		if count[0] != 0:
			flash('Correo electronico ya registrado', category='error')
			return render_template("sign_up.html")

		if len(request.form['password']) <8:
			flash('La contraseña debe tener un minimo de 8 caracteres', category="error")
			return render_template("sign_up.html")

		if request.form['password'] != request.form['password2']:
			flash('Las contraseñas no coinciden',category="error")
			return render_template("sign_up.html")

		sql = """insert into usuarios (email,password,nombre,apellido,tipo,nivel,fecha_registro) values ('%s',crypt('%s', gen_salt('bf')),'%s','%s',1,'%s',now());"""%(request.form['email'],request.form['password'],request.form['nombre'],request.form['apellido'],request.form['nivel'])

		cur.execute(sql)
		conn.commit()
		flash('Cuenta creada exitosamente', category='success')
		return redirect("/login")
	return render_template("sign_up.html")

@app.route('/logout')
def logout():
	session.pop('username', None)
	session.pop('user_id', None)
	session.pop('tipo', None)
	flash('Sesion Cerrada Correctamente',category='success')
	return redirect("/login")

@app.route('/admin')
def admin():
	if not 'username' in session:
		return redirect("/login")
	else:
		if session['tipo']!=2:
			return redirect("/")
		else:
			diaactual = date.today().strftime("%Y-%m-%d")
			sql = """select reservas.fecha, reservas.bloque,reservas.cancha ,reservas.jugador1, reservas.jugador2, reservas.invitado1, reservas.fecha_reserva from reservas, usuarios where disponible = false and fecha='%s' """%(diaactual)
			cur2.execute(sql)
			datos = cur2.fetchall()
			print(datos)
			return render_template("homeadmin.html",datos=datos)

@app.route('/admin1')
def admin1():
	if not 'username' in session:
		return redirect("/login")
	else:
		if session['tipo']!=2:
			return redirect("/")
		else:
			return render_template("generarfecha.html")

@app.route('/ver_reserva')
def ver_reserva():
	if not 'username' in session:
		return redirect("/login")
	else:
		if session['tipo']!=2:
			return redirect("/")
		else:
			sql="""select * from reservas where disponible = False order by fecha desc"""
			cur2.execute(sql)
			datos = cur2.fetchall()
			return render_template("vistareservas.html",datos=datos)

@app.route('/buscar_reserva')
def buscar_reserva():
	if not 'username' in session:
		return redirect("/login")
	else:
		if session['tipo']!=2:
			return redirect("/")
		else:
			return render_template("buscar.html")

@app.route('/elminar_reserva',methods=['POST','GET'])
def eliminar_reserva():
	if request.method == 'POST':
		if not 'username' in session:
			return redirect("/login")
		else:
			if session['tipo']!=2:
				return redirect("/")
			else:
				mail = str(request.form['mailr'])
				nombre = str(request.form['nombrer'])
				sql="""select id from usuarios where email = '%s'"""%(mail)
				cur2.execute(sql)
				dato = cur2.fetchone()
				if dato == None and nombre == None:
					return render_template("noexiste.html")
				elif dato == None and nombre != None:
					sql="""select * from reservas where invitado1 = '%s' order by fecha desc"""%(nombre)
					cur2.execute(sql)
					datos=cur2.fetchall()
					return render_template("tabla_eliminar1.html",datos=datos,nombre=nombre)
				else: #eliminar reserva completa hecha por usuario
					idjugador = int(dato[0])
					sql="""select * from reservas where jugador1 = '%s' order by fecha desc"""%(idjugador)
					cur2.execute(sql)
					datos = cur2.fetchall()
					return render_template("tabla_eliminar.html",datos=datos,mail=mail)
	else:
		return redirect("/")

@app.route('/conf_elim',methods=['POST','GET'])
def conf_elim():
	if request.method == 'POST':
		if not 'username' in session:
			return redirect("/login")
		else:
			if session['tipo']!=2:
				return redirect("/")
			else:
				idrecibida = int(request.form.get("idrec",""))
				sql = """update reservas set disponible = true, jugador1 = NULL, jugador2 = NULL, invitado1 = NULL ,tx1 = NULL , tipo_reserva = NULL, pago = NULL, fecha_reserva = NULL where id = '%s'"""%(idrecibida)
				cur2.execute(sql)
				conn.commit()
				flash('Reserva eliminada correctamente',category='success')
				return redirect("/")
	else:
		return redirect("/")

@app.route('/editar_res',methods=['POST','GET'])
def editar_res():
	if request.method == 'POST':
		if not 'username' in session:
			return redirect("/login")
		else:
			if session['tipo']!=2:
				return redirect("/")
			else:
				idrecibida = int(request.form.get("idrec",""))
				sql = """select * from reservas where id = '%s'"""%(idrecibida)
				cur2.execute(sql)
				datos = cur2.fetchall()
				sql = """select * from reservas where disponible = True order by fecha desc, bloque, cancha"""
				cur2.execute(sql)
				datos1 = cur2.fetchall()
				return render_template("editar.html",datos=datos, datos1=datos1,idrecibida=idrecibida)
	else:
		return redirect("/")

@app.route('/conf_edit',methods=['POST','GET'])
def conf_edit():
	if request.method == 'POST':
		if not 'username' in session:
			return redirect("/login")
		else:
			if session['tipo']!=2:
				return redirect("/")
			else:
				idrecibidas = request.form.get("idrec","")
				idnueva = int(idrecibidas)
				idvieja = int(request.form.get("idvieja",""))
				sql = """select * from reservas where id = '%s'"""%(idvieja)
				cur2.execute(sql)
				datos1 = cur2.fetchone()
				datos = list(datos1)
				print(datos)
				jugador1 = datos[4]
				#jugador2 = datos[5]
				#invitado1= datos[6]
				#invitado2= datos[7]
				tipo_reserva = datos[9]
				tx1 = datos[10]
				#tx2 = datos[11]
				pago = datos[12]
				#fecha_reserva = datos[13]
				if pago != None and tx1 != None:
					sql = """update reservas set disponible=False,jugador1 = '%s',jugador2 = NULL,invitado1=NULL,invitado2=NULL,tx1 = '%s',tx2=NULL,tipo_reserva='%s',pago='%s',fecha_reserva=NULL where id='%s'"""%(jugador1,tipo_reserva,tx1,pago,idnueva)
					cur2.execute(sql)
					conn.commit()
					sql = """update reservas set disponible = true, jugador1 = NULL, jugador2 = NULL, invitado1 = NULL ,tx1 = NULL,tx2= NULL , tipo_reserva = NULL, pago = NULL, fecha_reserva = NULL where id = '%s'"""%(idvieja)
					cur2.execute(sql)
					conn.commit()
					flash('El cambio de reserva se realizó correctamente',category='success')
					return redirect("/")
				elif pago != None and tx1 == None:
					sql = """update reservas set disponible=False,jugador1 = '%s',jugador2 = NULL,invitado1=NULL,invitado2=NULL,tx1 = NULL,tx2=NULL,tipo_reserva='%s',pago=NULL,fecha_reserva=NULL where id='%s'"""%(jugador1,tipo_reserva,pago,idnueva)
					cur2.execute(sql)
					conn.commit()
					sql = """update reservas set disponible = true, jugador1 = NULL, jugador2 = NULL, invitado1 = NULL ,tx1 = NULL,tx2= NULL , tipo_reserva = NULL, pago = NULL, fecha_reserva = NULL where id = '%s'"""%(idvieja)
					cur2.execute(sql)
					conn.commit()
					flash('El cambio de reserva se realizó correctamente',category='success')
					return redirect("/")
				else:
					sql = """update reservas set disponible=False,jugador1 = '%s',jugador2 = NULL,invitado1=NULL,invitado2=NULL,tx1 = NULL,tx2=NULL,tipo_reserva='%s',pago=NULL,fecha_reserva=NULL where id='%s'"""%(jugador1,tipo_reserva,idnueva)
					cur2.execute(sql)
					conn.commit()
					sql = """update reservas set disponible = true, jugador1 = NULL, jugador2 = NULL, invitado1 = NULL ,tx1 = NULL,tx2= NULL , tipo_reserva = NULL, pago = NULL, fecha_reserva = NULL where id = '%s'"""%(idvieja)
					cur2.execute(sql)
					conn.commit()
					flash('El cambio de reserva se realizó correctamente',category='success')
					return redirect("/")
	else:
		return redirect("/")

@app.route('/ver_usuarios')
def ver_usuarios():
	if not 'username' in session:
		return redirect("/login")
	else:
		if session['tipo']!=2:
			return redirect("/")
		else:
			sql="""select * from usuarios order by fecha_registro"""
			cur2.execute(sql)
			datos = cur2.fetchall()
			return render_template("vistausuarios.html",datos=datos)

@app.route('/init_day1', methods=['POST','GET'])
def init_day1():
	if request.method == 'POST':
		dia = request.form['diar']
		mes = request.form['mesr']
		anio = request.form['anior']
		date = anio+"-"+mes+"-"+dia
		if not 'username' in session:
			output = {"status": "-1", "msg": "No logged in"}
			return redirect("/login")
		else:
			if session['tipo']!=2:
				output = {"status": "-1", "msg": "Not admin"}
				return redirect("/")
			else:
				sql = """delete from reservas where fecha = '%s'"""%(date)
				cur.execute(sql)
				for i in range(1,7):
					cancha = 1
					sql = """insert into reservas (disponible,fecha,bloque,cancha) values (true,'%s','%s','%s');"""%(date,i,cancha)
					cur.execute(sql)
				for i in range(1,7):
					cancha = 2
					sql = """insert into reservas (disponible,fecha,bloque,cancha) values (true,'%s','%s','%s');"""%(date,i,cancha)
					cur.execute(sql)
				output = {"status": "1", "msg": "Executed"}
				flash('Dia generado correctamente',category='success')
				return redirect("/")
	else:
		return redirect("/")

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
				sql = """insert into reservas (disponible,fecha,bloque,cancha) values (true,'%s','%s','%s');"""%(date,i,cancha)
				cur.execute(sql)
			for i in range(1,7):
				cancha = 2
				sql = """insert into reservas (disponible,fecha,bloque,cancha) values (true,'%s','%s','%s');"""%(date,i,cancha)
				cur.execute(sql)
			output = {"status": "1", "msg": "Executed"}
			return jsonify(output)

@app.route('/get_disp/<date>', methods=['GET'])
def get_disp(date):
	if not 'username' in session:
		output = {"status": "-1", "msg": "No logged in"}
		return jsonify(output)
	else:
		sql = """select id, cancha, bloque, disponible, tipo_reserva from reservas where fecha = '%s' and cancha = '%s' ORDER BY bloque ASC;"""%(date,1)
		cur.execute(sql)
		array1 = cur.fetchall()
		sql = """select id, cancha, bloque, disponible, tipo_reserva from reservas where fecha = '%s' and cancha = '%s' ORDER BY bloque ASC;"""%(date,2)
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

	sql = """select id, cancha, bloque, disponible, tipo_reserva from reservas where fecha = '%s' and cancha = '%s' ORDER BY bloque ASC;"""%(fecha,1)
	cur.execute(sql)
	cancha1 = cur.fetchall()
	sql = """select id, cancha, bloque, disponible, tipo_reserva from reservas where fecha = '%s' and cancha = '%s' ORDER BY bloque ASC;"""%(fecha,2)
	cur.execute(sql)
	cancha2 = cur.fetchall()

	return render_template("tabla_reserva.html", dia_id=dia_id, dias=dias,cancha1=cancha1, cancha2=cancha2)

@app.route('/add_reserva', methods = ['POST','GET'])
def add_reserva():
	if request.method == 'POST':
		idrec = int(request.form.get("idreserva",""))
		sql = """SELECT disponible,tipo_reserva from reservas where id = '%s'"""%(idrec)
		cur2.execute(sql)
		tiporeserva = cur2.fetchone()
		disponibilidad = tiporeserva[0]
		tiporeserva1 = tiporeserva[1]#tenemos el numero para saber si es parcial o no
		if disponibilidad == True: #esta vacia(disponible totalmente)
			if not 'username' in session: #si no es usuario
				return redirect("/login")
			else:
				if session['tipo']!=2: #si es usuario normal
					sql = """SELECT nombre, apellido, nivel FROM usuarios WHERE id = '%s';"""%(session['user_id'])
					cur2.execute(sql)
					datosusuario = cur2.fetchall()
					nombre = datosusuario[0][0]
					apellido = datosusuario[0][1]
					nivelfinal = int(datosusuario[0][2])
					email = session['username']
					return render_template("datosuser.html",idrec=idrec,nombre=nombre,apellido=apellido,email=email,nivelfinal=nivelfinal)#se autocompleta
				else: #si es admin
					return render_template("datosres.html",idrec=idrec) #para completar
		else: #ya tiene una parcial
			if not 'username' in session: #si no es usuario
				return redirect("/login")
			else:
				if session['tipo'] != 2: #usuario normal
					sql = """SELECT jugador1 FROM reservas WHERE id = '%s'"""%(idrec)#id del jugador que tiene la reserva parcial
					cur2.execute(sql)
					idjugador1 = cur2.fetchone()
					idjugador = idjugador1[0]
					sql = """SELECT nombre,apellido,nivel FROM usuarios WHERE id = '%s';"""%(idjugador)#datos del jugador con la reserva parcial
					cur2.execute(sql)
					datosusuario = cur2.fetchall()
					nombre = datosusuario[0][0]
					apellido = datosusuario[0][1]
					nivelfinal = int(datosusuario[0][2])
					sql = """SELECT nombre, apellido FROM usuarios WHERE id = '%s';"""%(session['user_id'])
					cur2.execute(sql)
					datosusuario = cur2.fetchall()
					nombreses = datosusuario[0][0]
					apellidoses = datosusuario[0][1]
					emailses = session['username']
					return render_template("datosuser_p.html",idrec=idrec,nombre = nombre,apellido=apellido,nivelfinal=nivelfinal,nombreses=nombreses,apellidoses=apellidoses,emailses=emailses)
				else: #admin realiza reserva parcial
					sql = """SELECT jugador1 FROM reservas WHERE id = '%s'"""%(idrec)#id del jugador que tiene la reserva parcial
					cur2.execute(sql)
					idjugador1 = cur2.fetchone()
					idjugador = idjugador1[0]
					sql = """SELECT nombre,apellido,nivel FROM usuarios WHERE id = '%s';"""%(idjugador)#datos del jugador con la reserva parcial
					cur2.execute(sql)
					datosusuario = cur2.fetchall()
					nombre = datosusuario[0][0]
					apellido = datosusuario[0][1]
					nivelfinal = int(datosusuario[0][2])
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
				pago = int(request.form['opcionespag'])
				tipo = int(request.form.get("tipo_reserva"))

				if pago == 1:
					#URL Confirmation: https://asdfasdf/flow_callback/id_reserva/user_id/tipo_reserva/tx12
					#URL Return: https://asdfasdf/payment_confirmation/id_reserva
					url_confirmation = sirca_url + "/flow_callback/"+str(idrec)+"/"+str(idusuario)+"/"+str(tipo)+"/1"
					url_return = sirca_url + "/payment_confirmation/"+str(idrec)
					if tipo == 1:
						flow = flow_payment(str(idrec)+"_1","Reserva cancha",5000,session['username'],url_confirmation,url_return)
						print(flow)
					else:
						flow = flow_payment(idrec,"Reserva cancha",10000,session['username'],url_confirmation,url_return)
						print(flow)

					sql = """insert into transacciones (token,fecha,confirmed) values ('%s',now(),false);"""%(flow['token'])
					cur.execute(sql)
					conn.commit()

					return redirect(flow['url']+"?token="+flow['token'])

				else:
					if tipo == 1: #reserva parcial
						sql = """UPDATE reservas SET disponible = False, jugador1 = '%s' , tipo_reserva = 1 WHERE id = '%s'"""%(idusuario,idrec)
						cur2.execute(sql)
						conn.commit() #reserva parcial jugador registrado

						sql = """SELECT * FROM reservas WHERE id = %s"""%(idrec)
						cur.execute(sql)
						datos_reserva = cur.fetchone()
						fecha = datos_reserva['fecha']
						bloque = datos_reserva['bloque']
						mensaje = "Su reserva fue realizada con exito para el dia %s en el bloque %s."%(fecha,bloque)
						asunto = "Reserva realizada con exito"
						correo = session['username']

						confirmation(asunto, mensaje,correo)
						flash('Reserva realizada con exito', category='success')
						return redirect('/')
					else: #reserva completa
						sql = """UPDATE reservas SET disponible = False, jugador1 = '%s', tipo_reserva = 2 WHERE id = '%s'"""%(idusuario,idrec)
						cur2.execute(sql)
						conn.commit() #reserva completa jugador registrado

						sql = """SELECT * FROM reservas WHERE id = %s"""%(idrec)
						cur.execute(sql)
						datos_reserva = cur.fetchone()
						fecha = datos_reserva['fecha']
						bloque = datos_reserva['bloque']
						mensaje = "Su reserva fue realizada con exito para el dia %s en el bloque %s."%(fecha,bloque)
						asunto = "Reserva realizada con exito"
						correo = session['username']
						flash('Reserva realizada con exito', category='success')
						return redirect('/')

			else: #admin, reserva completa
				idrec = int(request.form.get("idreserva",""))
				nombre = request.form['nombrer']
				apellido = request.form['apellr']
				invitado1 = nombre + " " + apellido
				sql = """UPDATE reservas SET disponible = False, invitado1 = '%s',tipo_reserva = 2,pago = 3 WHERE id = '%s'"""%(invitado1,idrec)
				cur2.execute(sql)
				conn.commit() #reserva completa invitado1
				flash('Reserva realizada con exito',category='success')
				return redirect('/') #falta html para confirmar que se hizo la reserva

@app.route('/realizar_reserva_parcial', methods = ['POST','GET']) #completar la reserva parcial y guardarla en la base
def realizar_reserva_parcial():
	if request.method == 'POST':
		if not 'username' in session: #si no es usuario
			return redirect("/login")
		else:
			if session['tipo']!=2: #si es usuario normal
				idrec = int(request.form.get("idreserva",""))
				jugador2 = int(session['user_id']) #falta setear lo del pago
				pago = int(request.form['opcionespag'])
				if pago == 1:
					#URL Confirmation: https://asdfasdf/flow_callback/id_reserva/user_id/tipo_reserva/tx12
					#URL Return: https://asdfasdf/payment_confirmation/id_reserva
					url_confirmation = sirca_url + "/flow_callback/"+str(idrec)+"/"+str(jugador2)+"/2/2"
					url_return = sirca_url + "/payment_confirmation/"+str(idrec)
					flow = flow_payment(str(idrec)+"_2","Reserva cancha",5000,session['username'],url_confirmation,url_return)

					sql = """insert into transacciones (token,fecha,confirmed) values ('%s',now(),false);"""%(flow['token'])
					cur.execute(sql)
					conn.commit()

					return redirect(flow['url']+"?token="+flow['token'])


				else:
					sql = """UPDATE reservas SET jugador2 = '%s',tipo_reserva = 2 WHERE id = '%s'"""%(jugador2,idrec)
					cur2.execute(sql)
					conn.commit() #completar reserva parcial con otro jugador registrado, registrado/registrado
					sql = """SELECT * FROM reservas WHERE id = %s"""%(idrec)
					cur.execute(sql)
					datos_reserva = cur.fetchone()
					fecha = datos_reserva['fecha']
					bloque = datos_reserva['bloque']
					mensaje = "Su reserva parcial fue realizada con exito para el dia %s en el bloque %s."%(fecha,bloque)
					asunto = "Reserva realizada con exito"
					correo = session['username']

					confirmation(asunto, mensaje, correo)
					flash('Reserva realizada con exito', category='success')
					return redirect('/')
			else: #admin
				idrec = int(request.form.get("idreserva",""))
				nombre = request.form['nombrer']
				apellido = request.form['apellr']
				invitado1 = nombre + " " + apellido  #falta setear lo del pago
				sql = """UPDATE reservas SET invitado1 = '%s',tipo_reserva = 2 WHERE id = '%s'"""%(invitado1,idrec)
				cur2.execute(sql)
				conn.commit() #completar reserva parcial con un invitado, registrado/invitado
				flash('Reserva realizada con exito', category='success')
				return redirect('/')

def confirmation(asunto,mensaje,correo):
	msg = Message(asunto, sender='sirca@cuy.cl', recipients=[correo])
	msg.body = mensaje
	mail.send(msg)

@app.route("/forgot",methods=["GET","POST"])
def forgot():
	if request.method == 'POST':
		correo = request.form['email']
		sql ="select email from usuarios where email = '%s'" %correo
		cur2.execute(sql)
		correo2 = cur2.fetchone()
		print(correo2)
		print(correo2[0])
		if(correo2): #!= None
			key = secrets.token_hex(nbytes=16)
			user_reset = """INSERT INTO token (email,token_id, used) values ('%s','%s','%s')"""%(correo, key ,'FALSE')
			cur2.execute(user_reset)
			conn.commit()
			mensaje = "Para reestablecer su contraseña ingrese al siguiente link: www.sirca.cuy.cl/reset2/" + key
			confirmation("Restablecer contraseña",mensaje ,correo)
			print("Correo enviado")
			flash('Revise su correo electronico para continuar')
			return render_template("login.html")
		else:
			flash("Correo electronico no registrado",category="error")
	else:
		return render_template("forgot.html")

def validate_token(id):
	print("0")
	validate = """select * from token where token_id = '%s'"""%id
	cur2.execute(validate)
	exists = cur2.fetchone()
	validation = True
	print(type(exists))
	print("1")
	if len(exists) == 0:
		print("token invalido")
		validation = False
		return validation
	print("2")
	used = """select used from token where token_id = '%s'"""%id
	cur2.execute(used)
	usado = cur2.fetchone()
	print(usado)
	if usado[0]:
		print("token ya usado")
		validation = False
		return validation
	print("3")


	return validation

@app.route("/reset2/<id>", methods=['GET','POST'])
def reset2(id):
	sql = """select email from token where token_id = '%s'"""%id
	cur2.execute(sql)
	correo = cur2.fetchone()
	print(correo)
	print(id)
	if request.method == 'POST':
		if request.form["password"] != request.form["password2"]:
			flash("las contraseñas no coinciden",category='error')
			return render_template('reset2')
		if len(request.form["password"]) < 8:
			flash("la contraseña debe tener un minimo de 8 caracteres",category='error')
			return render_template('reset2.html')
		pwd = request.form["password"]
		print(pwd)
		print(correo[0])

		user_reset = """update usuarios set password =crypt('%s', gen_salt('bf')) where email = '%s'"""%(pwd,correo[0])
		cur.execute(user_reset)
		conn.commit()

		token_used = """update token set used = True"""
		cur.execute(token_used)
		conn.commit()

		flash("Contraseña actualizada con exito",category='success')
		return 	redirect("/login")
	else:
		if validate_token(id):
			return render_template("reset2.html")
		else:
			flash('Solicite un nuevo enlace para restablecer la contraseña', category='error')
			return redirect("/login")

@app.route('/profile', methods = ['POST','GET']) #ver/actualizar datos del usuario y gurdar en la base
def profile():
	if request.method == 'POST':
		sql = """SELECT nombre, apellido, nivel, email FROM usuarios WHERE id = '%s';"""%(session['user_id'])
		cur.execute(sql)
		datosusuario = cur.fetchone()
		nombre = datosusuario['nombre']
		apellido = datosusuario['apellido']
		nivelactual = int(datosusuario['nivel'])
		email = datosusuario['email']

		if int(request.form['nivelfinal']) == nivelactual:
			nivelfinal = request.form['nivelfinal']
			if request.form["password"] != request.form["password2"]:
				flash("las contraseñas no coinciden",category='error')
				return render_template("profile.html",nombre=nombre,apellido=apellido,email=email,nivelfinal=nivelfinal)#se autocompleta
			if len(request.form["password"]) == 0:
				flash("debe modificar algun campo",category='error')
				return render_template("profile.html",nombre=nombre,apellido=apellido,email=email,nivelfinal=nivelfinal)#se autocompleta
			if len(request.form["password"]) < 8 and len(request.form["password"]) > 0:
				flash("la contraseña debe tener un minimo de 8 caracteres",category='error')
				return render_template("profile.html",nombre=nombre,apellido=apellido,email=email,nivelfinal=nivelfinal)#se autocompleta


			pwd = request.form["password"]
			print(pwd)
			sql = """update usuarios set password =crypt('%s', gen_salt('bf')) where email = '%s'"""%(pwd,email)
			cur.execute(sql)
			conn.commit()
			flash("Contraseña actualizada con exito",category='success')
			nivelfinal = nivelactual
			return render_template("profile.html",nombre=nombre,apellido=apellido,email=email,nivelfinal=nivelfinal)#se autocompleta

		nivelfinal = request.form['nivelfinal']
		if request.form["password"] != request.form["password2"]:
			flash("las contraseñas no coinciden",category='error')
			return render_template("profile.html",nombre=nombre,apellido=apellido,email=email,nivelfinal=nivelfinal)#se autocompleta
		if len(request.form["password"]) == 0:
			nuevolevel = int(request.form["nivelfinal"])
			print(nuevolevel)
			sql = """update usuarios set nivel = '%s' where email = '%s'"""%(nuevolevel,email)
			cur.execute(sql)
			conn.commit()
			nivelfinal = nuevolevel
			flash("Nivel actualizado con exito",category='success')
			return render_template("profile.html",nombre=nombre,apellido=apellido,email=email,nivelfinal=nivelfinal)#se autocompleta
		if len(request.form["password"]) < 8 and len(request.form["password"]) > 0:
			flash("la contraseña debe tener un minimo de 8 caracteres",category='error')
			return render_template("profile.html",nombre=nombre,apellido=apellido,email=email,nivelfinal=nivelfinal)#se autocompleta

		nuevolevel = int(request.form["nivelfinal"])
		print(nuevolevel)
		pwd = request.form["password"]
		print(pwd)
		sql = """update usuarios set password =crypt('%s', gen_salt('bf')), nivel = '%s' where email = '%s'"""%(pwd, nuevolevel,email)
		cur.execute(sql)
		conn.commit()
		nivelfinal = nuevolevel
		flash("Datos actualizados con exito",category='success')
		return render_template("profile.html",nombre=nombre,apellido=apellido,email=email,nivelfinal=nivelfinal)#se autocompleta

	cur.execute("""SELECT nombre, apellido, nivel, email FROM usuarios WHERE id = '%s';"""%(session['user_id']))
	datosusuario = cur.fetchone()
	nombre = datosusuario['nombre']
	apellido = datosusuario['apellido']
	nivelfinal = datosusuario['nivel']
	email = datosusuario['email']
	return render_template("profile.html",nombre=nombre,apellido=apellido,email=email,nivelfinal=nivelfinal)#se autocompleta

@app.route('/flow_callback/<id_reserva>/<user_id>/<tipo_reserva>/<tx12>', methods = ['POST'])
#URL Confirmation: https://asdfasdf/flow_callback/id_reserva/user_id/tipo_reserva/tx12
def flow_callback(id_reserva,user_id,tipo_reserva,tx12):
	token = request.form['token']
	payment_status = flow_getStatus(token)
	if payment_status['status'] == 2:
		sql = """UPDATE transacciones SET confirmed = true WHERE token = '%s'"""%(token)
		cur.execute(sql)
		conn.commit()
		idrec = int(id_reserva)
		idusuario = int(user_id)
		tipo = int(tipo_reserva)

		sql = """SELECT email FROM usuarios WHERE id = '%s';"""%(idusuario)#datos del jugador con la reserva parcial
		cur.execute(sql)
		datos_usuario = cur.fetchone()
		datos_usuario['email']
		if int(tx12) == 1:
			if tipo == 1: #reserva parcial
				sql = """UPDATE reservas SET disponible = False, jugador1 = '%s', tx1 = '%s' , tipo_reserva = 1 WHERE id = '%s'"""%(idusuario,token,idrec)
				cur2.execute(sql)
				conn.commit() #reserva parcial jugador registrado

				sql = """SELECT * FROM reservas WHERE id = %s"""%(idrec)
				cur.execute(sql)
				datos_reserva = cur.fetchone()
				fecha = datos_reserva['fecha']
				bloque = datos_reserva['bloque']
				mensaje = "Su reserva fue realizada con exito para el dia %s en el bloque %s."%(fecha,bloque)
				asunto = "Reserva realizada con exito"
				correo = datos_usuario['email']

				confirmation(asunto, mensaje,correo)
				flash('Reserva realizada con exito', category='success')
				return redirect('/')
			else: #reserva completa
				sql = """UPDATE reservas SET disponible = False, jugador1 = '%s', tx1 = '%s', tipo_reserva = 2 WHERE id = '%s'"""%(idusuario,token,idrec)
				cur2.execute(sql)
				conn.commit() #reserva completa jugador registrado

				sql = """SELECT * FROM reservas WHERE id = %s"""%(idrec)
				cur.execute(sql)
				datos_reserva = cur.fetchone()
				fecha = datos_reserva['fecha']
				bloque = datos_reserva['bloque']
				mensaje = "Su reserva fue realizada con exito para el dia %s en el bloque %s."%(fecha,bloque)
				asunto = "Reserva realizada con exito"
				correo = datos_usuario['email']
				confirmation(asunto, mensaje,correo)
				flash('Reserva realizada con exito',category='success')
				return redirect('/')
		else:
			sql = """UPDATE reservas SET jugador2 = '%s',tipo_reserva = 2, tx2='%s' WHERE id = '%s'"""%(idusuario,token,idrec)
			cur2.execute(sql)
			conn.commit() #completar reserva parcial con otro jugador registrado, registrado/registrado
			sql = """SELECT * FROM reservas WHERE id = %s"""%(idrec)
			cur.execute(sql)
			datos_reserva = cur.fetchone()
			fecha = datos_reserva['fecha']
			bloque = datos_reserva['bloque']
			mensaje = "Su reserva parcial fue realizada con exito para el dia %s en el bloque %s."%(fecha,bloque)
			asunto = "Reserva realizada con exito"
			correo = datos_usuario['email']

			confirmation(asunto, mensaje, correo)
			flash('Reserva realizada con exito',category='success')
			return redirect('/')
	return "Ok :)"

@app.route('/payment_confirmation/<id_reserva>', methods = ['POST'])
def payment_confirmation(id_reserva):
	flash('Reserva realizada con exito', category='success')
	return redirect('/')
