from flask import Flask
from flask_mail import Mail

app = Flask(__name__)
from app import views
app.config['MAIL_SERVER'] = 'mail.cuy.cl'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'sirca@cuy.cl'
app.config['MAIL_DEFAULT_SENDER'] = 'sirca@cuy.cl'
app.config['MAIL_PASSWORD'] = 'OXurpKj708'
app.config['MAIL_USE_TLS'] = True
#app.config['MAIL_USE_SSL'] = True
mail = Mail(app)
