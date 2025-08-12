import os
import logging

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, AnonymousUserMixin
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix


class Base(DeclarativeBase):
    pass


class Anonymous(AnonymousUserMixin):
    """Custom anonymous user class with role-based methods."""
    
    def is_admin(self):
        return False
    
    def is_judge(self):
        return False
    
    def can_submit(self):
        return False


db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)


logging.basicConfig(level=logging.DEBUG)


database_url = os.environ.get("DATABASE_URL")
if database_url and "neon.tech" in database_url:

    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///mohreels.db"
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url or "sqlite:///mohreels.db"
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# configure uploads
app.config['UPLOAD_FOLDER'] = 'videos'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  


db.init_app(app)
login_manager.init_app(app)
login_manager.anonymous_user = Anonymous
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))


@app.template_filter('datetime')
def datetime_filter(dt, format='%Y-%m-%d %H:%M'):
    """Format a datetime object."""
    if dt is None:
        return ""
    return dt.strftime(format)

with app.app_context():
    # Import models to ensure tables are created
    import models
    try:
        db.create_all()

        from models import User
        from werkzeug.security import generate_password_hash
        
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@mohreels.local',
                full_name='Administrator',
                password_hash=generate_password_hash('admin123'),
                bio='Default admin user'
            )
            db.session.add(admin)
            db.session.commit()
            app.logger.info("Created default admin user: admin/admin123")
    except Exception as e:
        app.logger.error(f"Database initialization error: {e}")

# Import routes
import routes
