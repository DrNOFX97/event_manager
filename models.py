from datetime import date
from database import db

# Raise an error if database is not initialized
if db is None:
    raise RuntimeError("Database not initialized. Call init_database() in your app setup first.")

class Utilizador(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome_completo = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)

class Evento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    data = db.Column(db.Date, nullable=False)
    duracao = db.Column(db.Integer, nullable=False)
    formadora = db.Column(db.String(100), nullable=True)
    
    # Relationship with Participante
    participantes = db.relationship('Participante', 
        back_populates='evento', 
        cascade='all, delete-orphan'
    )

class Participante(db.Model):
    __tablename__ = 'participante'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    
    # Foreign key to link Participante with Evento
    evento_id = db.Column(db.Integer, db.ForeignKey('evento.id', ondelete='CASCADE'), nullable=False)
    
    # Relationship with Evento
    evento = db.relationship('Evento', back_populates='participantes')
    
    status = db.Column(db.String(20), default='pendente')
    certificado_gerado = db.Column(db.Boolean, default=False)
    certificado_enviado = db.Column(db.Boolean, default=False)
    
    # Unique constraint to prevent duplicate participants in the same event
    __table_args__ = (
        db.UniqueConstraint('email', 'evento_id', name='_email_evento_uc'),
    )