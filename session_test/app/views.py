from app import app
from flask import render_template,request,redirect,session
import psycopg2
from app import configuraciones

conn = psycopg2.connect("dbname=%s user=%s password=%s host=%s port=%s"%(configuraciones.db_database,configuraciones.db_user,configuraciones.db_passwd,configuraciones.db_host,configuraciones.db_port))
cur = conn.cursor()

app.secret_key = configuraciones.session_key

@app.route('/')
def home():
	if not 'username' in session:
		return redirect("/login")
	else:
		return "hola holi"


@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		sql = """select email from usuarios where email = '%s' and password = crypt('%s', password);"""%(request.form['email'],request.form['password'])
		cur.execute(sql)
		print(sql)
		array = cur.fetchone()
		print(array)
		if array:
			session['username']=array[0]
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
	return redirect("/login")