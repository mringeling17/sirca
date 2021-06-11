from flask import Flask
from flask_mail import Mail

app = Flask(__name__)
from app import views
app.config['MAIL_SERVER'] = 'sirca.cuy.cl'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'sirca@cuy.cl'
app.config['EMAIL_PASSWORD'] = 'OXurpKj708'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)
