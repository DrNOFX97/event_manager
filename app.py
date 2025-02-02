import os
import logging
from datetime import date
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Compatibility import for url_quote
try:
    from werkzeug.urls import url_quote
except ImportError:
    from werkzeug.urls import quote as url_quote

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get base directory
basedir = os.path.abspath(os.path.dirname(__file__))

load_dotenv()  # Carrega as variáveis do arquivo .env

def create_app():
    # Create Flask application
    app = Flask(__name__)
    
    # Configure application
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "event_manager.db")}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.urandom(24)  # Secure random secret key
    
    # Configure upload folder
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    
    # Ensure uploads directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Configurações do aplicativo
    app.config['EMAIL_USER'] = os.environ.get('EMAIL_USER')  # Email do remetente
    app.config['EMAIL_PASSWORD'] = os.environ.get('EMAIL_PASSWORD')  # Senha do email
    app.config['SMTP_SERVER'] = 'smtp.gmail.com'  # Servidor SMTP
    app.config['SMTP_PORT'] = 587  # Porta SMTP

    # Import and initialize database
    from database import db, init_db
    init_db(app)
    migrate = Migrate(app, db)  # Initialize Flask-Migrate

    # Register blueprints
    from routes import bp
    app.register_blueprint(bp)

    app.config['BASE_DIR'] = basedir

    return app

# Create the application
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)