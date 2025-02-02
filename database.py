from flask import Flask
import os
import logging
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import OperationalError
from sqlalchemy.sql import text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create SQLAlchemy instance
db = SQLAlchemy()

def migrate_database(app):
    """
    Perform database migration to add missing columns
    """
    with app.app_context():
        try:
            # Check if formadora column exists
            db.session.execute(text("SELECT formadora FROM evento LIMIT 1"))
        except OperationalError:
            # Column does not exist, add it
            try:
                logger.info("Adding 'formadora' column to evento table")
                db.session.execute(text("ALTER TABLE evento ADD COLUMN formadora VARCHAR(100)"))
                db.session.commit()
                logger.info("Successfully added 'formadora' column")
            except Exception as e:
                logger.error(f"Error adding 'formadora' column: {e}")
                db.session.rollback()

def init_db(app: Flask):
    """
    Initialize the database for the given Flask application.
    
    :param app: Flask application instance
    """
    # Use the same database URI as in app.py
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'event_manager.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Add secret key configuration
    app.config['SECRET_KEY'] = os.urandom(24)
    
    # Initialize the database with the app
    db.init_app(app)
    
    # Create all database tables within the application context
    with app.app_context():
        try:
            db.create_all()
            logger.info("Database tables created successfully")
            
            # Perform migration
            migrate_database(app)
            
            # Log existing tables
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            logger.info(f"Existing tables: {tables}")
        except Exception as e:
            logger.error(f"Error creating database tables: {e}", exc_info=True)
            raise

def get_db():
    """
    Retrieve the SQLAlchemy database instance.
    
    :return: SQLAlchemy database instance or None
    """
    return db