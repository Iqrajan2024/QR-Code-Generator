from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_mail import Mail,Message 

db= SQLAlchemy()


def create_app():
   
    app= Flask(__name__,template_folder='templates')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///./database.db'
    
    app.config['SECRET_KEY'] = 'THISISASECRETKEY'
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'your_email@gmail.com'
    app.config['MAIL_PASSWORD'] = 'your_email_password'
    QR_CODE_DIR = 'static/qr_codes'
    app.config['QR_CODE_DIR'] = QR_CODE_DIR
   
    db.init_app(app)

    mail = Mail(app)


    login_manager = LoginManager()
    login_manager.init_app(app)

    from models import User

    @login_manager.user_loader
    def load_user(uid):
        return User.query.get(uid)
    
    bcrypt = Bcrypt(app)


    from routes import register_routes
    register_routes(app,db,bcrypt)
    migrate=Migrate(app,db)

    return app



