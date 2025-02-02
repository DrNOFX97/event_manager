import logging
from datetime import date, datetime

from flask import (
    Blueprint, 
    render_template, 
    request, 
    flash, 
    redirect, 
    url_for, 
    current_app,
    send_file,
    jsonify
)
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import inspect

from models import db, Evento, Participante, Utilizador
import pandas as pd
from werkzeug.utils import secure_filename
import os
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.colors import black, HexColor
from reportlab.pdfgen import canvas
from PIL import Image
from reportlab.lib.utils import ImageReader
from textwrap import wrap
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# Create the blueprint
bp = Blueprint('main', __name__)

# Configure logging
logger = logging.getLogger(__name__)

# Helper functions for certificate generation
def calcular_altura_proporcional(largura_original, altura_original, nova_largura):
    """
    Calculate proportional height for image resizing
    """
    return int((altura_original / largura_original) * nova_largura)

def formatar_data(data):
    """
    Format date to a readable string
    """
    return data.strftime("%d de %B de %Y")

def criar_certificado_pdf(nome, titulo_evento, duracao, data, formadora, basedir, evento_id=None, participante_id=None):
    """
    Create a PDF certificate with detailed formatting
    
    :param nome: Name of participant
    :param titulo_evento: Event title
    :param duracao: Event duration
    :param data: Event date
    :param formadora: Event instructor
    :param basedir: Base directory for file paths
    :param evento_id: Optional event ID for filename
    :param participante_id: Optional participant ID for filename
    """
    # Ensure absolute path for certificados directory
    certificados_dir = os.path.abspath(os.path.join(basedir, 'uploads', 'certificados'))
    
    # Log detailed directory information
    logger.info(f"Base directory: {basedir}")
    logger.info(f"Certificados directory (absolute): {certificados_dir}")
    
    # Ensure directory exists with full permissions
    try:
        os.makedirs(certificados_dir, exist_ok=True)
        
        # Check directory permissions
        if not os.access(certificados_dir, os.W_OK):
            logger.error(f"No write permissions for directory: {certificados_dir}")
            # Attempt to change permissions
            try:
                os.chmod(certificados_dir, 0o755)
                logger.info(f"Updated directory permissions for: {certificados_dir}")
            except Exception as perm_error:
                logger.error(f"Failed to update directory permissions: {perm_error}")
        
        # Log directory details
        logger.info(f"Directory exists: {os.path.exists(certificados_dir)}")
        logger.info(f"Directory is writable: {os.access(certificados_dir, os.W_OK)}")
        logger.info(f"Directory contents: {os.listdir(certificados_dir)}")
    except Exception as dir_error:
        logger.error(f"Error creating/checking directory: {dir_error}")
        raise
    
    # Use consistent filename if evento_id and participante_id are provided
    if evento_id is not None and participante_id is not None:
        nome_arquivo = os.path.join(certificados_dir, f'certificado_{evento_id}_{participante_id}.pdf')
    else:
        # Fallback to original naming if IDs are not provided
        nome_arquivo = os.path.join(certificados_dir, f"certificado_{nome.replace(' ', '_')}.pdf")
    
    # Log filename with full path
    logger.info(f"Attempting to create certificate at: {nome_arquivo}")
    
    try:
        c = canvas.Canvas(nome_arquivo, pagesize=landscape(A4))
        largura, altura = landscape(A4)

        # Adicionar fundo suave em verde
        c.setFillColor(HexColor("#e6f9e6"))
        c.rect(0, 0, largura, altura, fill=True)

        # Adicionar borda com cantos arredondados
        c.setStrokeColor(HexColor("#4CAF50"))
        c.setLineWidth(5)
        c.roundRect(10, 10, largura - 20, altura - 20, radius=20)

        # Define logo path 
        logo_path = "/Users/f.nuno/Downloads/Logo AR da TERRA com rebordo.png"
        
        # Log logo path
        logger.info(f"Logo path: {logo_path}")
        logger.info(f"Logo exists: {os.path.exists(logo_path)}")

        # Obter as dimensões do logo
        with Image.open(logo_path) as img:
            largura_logo, altura_logo = img.size

        # Definir a largura desejada para o logo
        largura_desejada = 100
        altura_desejada = calcular_altura_proporcional(largura_logo, altura_logo, largura_desejada)

        # Ajustar a posição do logo para evitar corte
        c.drawImage(logo_path, largura / 2 - largura_desejada / 2, altura - altura_desejada - 30,  
                     width=largura_desejada, height=altura_desejada, mask='auto')

        # Adicionar título do certificado
        c.setFont("Helvetica-Bold", 36)
        c.setFillColor(HexColor("#388E3C"))
        c.drawCentredString(largura / 2, altura - 210, "Certificado de Participação")

        # Adicionar informações do certificado
        c.setFont("Helvetica", 20)
        c.setFillColor(black)
        c.drawCentredString(largura / 2, altura - 250, "Certifica-se que")

        c.setFont("Helvetica-Bold", 28)
        c.drawCentredString(largura / 2, altura - 300, nome)

        c.setFont("Helvetica", 20)
        data_formatada = formatar_data(data)
        c.drawCentredString(largura / 2, altura - 350, f"Participou na Masterclass \"{titulo_evento}\",")
        c.drawCentredString(largura / 2, altura - 375, f"que teve a duração de {duracao} minutos em {data_formatada},")
        c.drawCentredString(largura / 2, altura - 400, f"que foi ministrada pela formadora {formadora}.")

        # Adicionar uma linha de assinatura
        c.setStrokeColor(black)
        c.setLineWidth(2)
        c.line(100, altura - 450, largura - 100, altura - 450)
        c.setFont("Helvetica-Oblique", 18)
        c.drawCentredString(largura / 2, altura - 470, "Assinatura")

        # Ensure file is saved with full write permissions
        c.save()
        
        # Verify file was created and set permissions
        if os.path.exists(nome_arquivo):
            try:
                os.chmod(nome_arquivo, 0o666)  # Full read/write permissions
                logger.info(f"Certificate successfully created: {nome_arquivo}")
                logger.info(f"Certificate file size: {os.path.getsize(nome_arquivo)} bytes")
            except Exception as perm_error:
                logger.error(f"Failed to set file permissions: {perm_error}")
        else:
            logger.error(f"Failed to create certificate: {nome_arquivo}")
        
        return nome_arquivo
    
    except Exception as e:
        logger.error(f"Error creating certificate: {str(e)}", exc_info=True)
        raise

@bp.route('/')
def index():
    try:
        eventos = Evento.query.all()
        logger.info(f"Fetched {len(eventos)} eventos for landing page")
        return render_template('menu_principal.html', eventos=eventos)
    except Exception as e:
        logger.error(f"Error in index route: {e}")
        flash(f'Erro ao carregar página inicial: {e}', 'error')
        return render_template('menu_principal.html', eventos=[])

@bp.route('/eventos')
def eventos():
    try:
        # Check database connection and tables
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        logger.info(f"Database tables: {tables}")
        
        # Check table columns
        columns = inspector.get_columns('evento')
        column_names = [col['name'] for col in columns]
        logger.info(f"Evento table columns: {column_names}")
        
        # Dynamically build query to handle missing columns
        query = db.session.query(Evento)
        
        eventos = query.all()
        logger.info(f"Fetched {len(eventos)} eventos from the database")
        
        # Log details of each event
        for evento in eventos:
            # Safely log event details
            event_details = {
                'id': evento.id,
                'nome': evento.nome,
                'data': evento.data,
                'duracao': evento.duracao
            }
            # Only add formadora if it exists
            if hasattr(evento, 'formadora'):
                event_details['formadora'] = evento.formadora
            
            logger.info(f"Event: {event_details}")
        
        return render_template('eventos.html', eventos=eventos)
    except Exception as e:
        logger.error(f"Error listing eventos: {e}", exc_info=True)
        flash(f'Erro ao listar eventos: {e}', 'error')
        return render_template('eventos.html', eventos=[])

@bp.route('/utilizadores')
def utilizadores():
    try:
        utilizadores = Utilizador.query.all()
        logger.info(f"Fetched {len(utilizadores)} utilizadores from the database")
        
        # Log details of each user
        for utilizador in utilizadores:
            logger.info(f"User: {utilizador.nome_completo}, Email: {utilizador.email}")
        
        return render_template('utilizadores.html', utilizadores=utilizadores)
    except Exception as e:
        logger.error(f"Error listing utilizadores: {e}")
        flash(f'Erro ao listar utilizadores: {e}', 'error')
        return render_template('utilizadores.html', utilizadores=[])

@bp.route('/criar_evento', methods=['GET', 'POST'])
def criar_evento():
    if request.method == 'POST':
        try:
            # Get form data
            nome = request.form.get('nome')
            data_str = request.form.get('data')
            duracao = request.form.get('duracao')
            formadora = request.form.get('formadora')
            
            # Parse date with more robust method
            data = datetime.strptime(data_str, '%d/%m/%y').date()
            
            # Create new event
            novo_evento = Evento(
                nome=nome, 
                data=data, 
                duracao=int(duracao),
                formadora=formadora if formadora != 'Outro' else 'Ana Rita Vieira'
            )
            
            # Add and commit
            db.session.add(novo_evento)
            db.session.commit()
            
            # Log details
            logger.info(f"New event created: {nome}, Date: {data}, Duration: {duracao}, Formadora: {novo_evento.formadora}")
            
            flash('Evento criado com sucesso!', 'success')
            return redirect(url_for('main.eventos'))
        
        except ValueError as e:
            logger.error(f"ValueError in criar_evento: {str(e)}")
            flash(f'Dados inválidos. Por favor, verifique os campos: {str(e)}', 'error')
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Unexpected error in criar_evento: {str(e)}", exc_info=True)
            flash('Erro inesperado ao criar evento.', 'error')
    
    return render_template('criar_evento.html')

@bp.route('/editar_evento/<int:id>', methods=['GET', 'POST'])
def editar_evento(id):
    try:
        # Find the event
        evento = Evento.query.get_or_404(id)
        
        if request.method == 'POST':
            # Get form data
            nome = request.form.get('nome')
            data_str = request.form.get('data')
            duracao = request.form.get('duracao')
            formadora = request.form.get('formadora')
            
            # Log received form data for debugging
            logger.info(f"Received form data: nome={nome}, data={data_str}, duracao={duracao}, formadora={formadora}")
            
            # Validate inputs
            if not all([nome, data_str, duracao]):
                flash('Todos os campos são obrigatórios.', 'error')
                return render_template('editar_evento.html', evento=evento)
            
            try:
                # Parse date with more robust method
                data = datetime.strptime(data_str, '%d/%m/%y').date()
            except ValueError:
                flash('Formato de data inválido. Use dd/mm/aa.', 'error')
                return render_template('editar_evento.html', evento=evento)
            
            try:
                duracao = int(duracao)
                if duracao < 30:
                    raise ValueError("Duração mínima é 30 minutos")
            except ValueError:
                flash('Duração inválida. Deve ser um número inteiro de 30 em 30 minutos.', 'error')
                return render_template('editar_evento.html', evento=evento)
            
            # Log current event state before update
            logger.info(f"Current event state before update: nome={evento.nome}, data={evento.data}, duracao={evento.duracao}, formadora={evento.formadora}")
            
            # Update event details
            evento.nome = nome
            evento.data = data
            evento.duracao = duracao
            
            # Set formadora, defaulting to "Ana Rita Vieira" if not specified
            evento.formadora = formadora if formadora != 'Outro' else 'Ana Rita Vieira'
            
            # Log event state after update
            logger.info(f"Event state after update: nome={evento.nome}, data={evento.data}, duracao={evento.duracao}, formadora={evento.formadora}")
            
            try:
                db.session.commit()
                logger.info(f"Event updated successfully: {nome}")
                flash('Evento atualizado com sucesso!', 'success')
                return redirect(url_for('main.eventos'))
            except Exception as commit_error:
                db.session.rollback()
                logger.error(f"Error committing event update: {str(commit_error)}")
                flash(f'Erro ao salvar evento: {str(commit_error)}', 'error')
        
        return render_template('editar_evento.html', evento=evento)
    
    except SQLAlchemyError as e:
        logger.error(f"Database error editing event: {str(e)}")
        db.session.rollback()
        flash(f'Erro ao editar evento: {str(e)}', 'error')
    except Exception as e:
        logger.error(f"Unexpected error editing event: {str(e)}")
        flash(f'Erro inesperado: {str(e)}', 'error')
    
    return redirect(url_for('main.eventos'))

@bp.route('/adicionar_utilizador', methods=['GET', 'POST'])
def adicionar_utilizador():
    if request.method == 'POST':
        try:
            # Get form data
            nome_completo = request.form.get('nome_completo')
            email = request.form.get('email')
            
            # Validate input
            if not nome_completo or not email:
                flash('Nome completo e email são obrigatórios.', 'error')
                return render_template('adicionar_utilizador.html')
            
            # Check if email already exists
            existing_user = Utilizador.query.filter_by(email=email).first()
            if existing_user:
                flash('Este email já está registado.', 'error')
                return render_template('adicionar_utilizador.html')
            
            # Create new user
            novo_utilizador = Utilizador(nome_completo=nome_completo, email=email)
            
            # Add to database
            db.session.add(novo_utilizador)
            db.session.commit()
            
            logger.info(f"New user added: {nome_completo}")
            flash('Utilizador adicionado com sucesso!', 'success')
            return redirect(url_for('main.utilizadores'))
        
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Database error adding user: {str(e)}")
            flash(f'Erro ao adicionar utilizador: {str(e)}', 'error')
        except Exception as e:
            logger.error(f"Unexpected error adding user: {str(e)}")
            flash(f'Erro inesperado: {str(e)}', 'error')
    
    return render_template('adicionar_utilizador.html')

@bp.route('/editar_utilizador/<int:id>', methods=['GET', 'POST'])
def editar_utilizador(id):
    utilizador = Utilizador.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Get form data
            nome_completo = request.form.get('nome_completo')
            email = request.form.get('email')
            
            # Validate input
            if not nome_completo or not email:
                flash('Nome completo e email são obrigatórios.', 'error')
                return render_template('editar_utilizador.html', utilizador=utilizador)
            
            # Check if email already exists (excluding current user)
            existing_user = Utilizador.query.filter(
                Utilizador.email == email, 
                Utilizador.id != id
            ).first()
            
            if existing_user:
                flash('Este email já está registado.', 'error')
                return render_template('editar_utilizador.html', utilizador=utilizador)
            
            # Update user details
            utilizador.nome_completo = nome_completo
            utilizador.email = email
            
            db.session.commit()
            
            logger.info(f"User updated: {nome_completo}")
            flash('Utilizador atualizado com sucesso!', 'success')
            return redirect(url_for('main.utilizadores'))
        
        except SQLAlchemyError as e:
            logger.error(f"Database error updating user: {str(e)}")
            db.session.rollback()
            flash(f'Erro ao atualizar utilizador: {str(e)}', 'error')
        except Exception as e:
            logger.error(f"Unexpected error updating user: {str(e)}")
            flash(f'Erro inesperado: {str(e)}', 'error')
    
    return render_template('editar_utilizador.html', utilizador=utilizador)

@bp.route('/apagar_utilizador/<int:id>', methods=['POST'])
def apagar_utilizador(id):
    try:
        # Find the user
        utilizador = Utilizador.query.get_or_404(id)
        
        # Log details before deletion
        logger.info(f"Attempting to delete user: {utilizador.nome_completo}")
        
        # Delete the user
        db.session.delete(utilizador)
        db.session.commit()
        
        # Log successful deletion
        logger.info(f"User deleted successfully: {utilizador.nome_completo}")
        
        flash('Utilizador apagado com sucesso!', 'success')
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemyError in apagar_utilizador: {str(e)}")
        db.session.rollback()
        flash(f'Erro ao apagar utilizador: {str(e)}', 'error')
    except Exception as e:
        logger.error(f"Unexpected error in apagar_utilizador: {str(e)}")
        flash(f'Erro inesperado: {str(e)}', 'error')
    
    return redirect(url_for('main.utilizadores'))

@bp.route('/detalhe_evento/<int:id>')
def detalhe_evento(id):
    evento = Evento.query.get_or_404(id)
    participantes = Participante.query.filter_by(evento_id=id).all()
    return render_template('detalhe_evento.html', evento=evento, participantes=participantes)

@bp.route('/adicionar_participantes/<int:evento_id>', methods=['GET', 'POST'])
def adicionar_participantes(evento_id):
    try:
        # Find the event
        evento = Evento.query.get_or_404(evento_id)
        
        # Get all users for the lista tab
        utilizadores = Utilizador.query.all()
        
        if request.method == 'POST':
            # Check which action was triggered
            action = request.form.get('action')
            
            if action == 'adicionar_lista':
                # Adding participants from user list
                utilizador_ids = request.form.getlist('utilizadores')
                
                if not utilizador_ids:
                    flash('Nenhum utilizador selecionado.', 'error')
                    return redirect(url_for('main.adicionar_participantes', evento_id=evento_id))
                
                added_count = 0
                for utilizador_id in utilizador_ids:
                    utilizador = Utilizador.query.get(utilizador_id)
                    
                    # Check if participant already exists for this event
                    existing_participante = Participante.query.filter_by(
                        email=utilizador.email, 
                        evento_id=evento_id
                    ).first()
                    
                    if not existing_participante:
                        # Create new participant for this event
                        novo_participante = Participante(
                            nome=utilizador.nome_completo, 
                            email=utilizador.email, 
                            evento_id=evento_id
                        )
                        db.session.add(novo_participante)
                        added_count += 1
                
                db.session.commit()
                flash(f'{added_count} participante(s) adicionado(s) ao evento.', 'success')
                return redirect(url_for('main.detalhe_evento', id=evento_id))
            
            elif action == 'importar_ficheiro':
                # Importing participants from file
                if 'ficheiro' not in request.files:
                    flash('Nenhum ficheiro enviado.', 'error')
                    return redirect(url_for('main.adicionar_participantes', evento_id=evento_id))
                
                file = request.files['ficheiro']
                
                if file.filename == '':
                    flash('Nenhum ficheiro selecionado.', 'error')
                    return redirect(url_for('main.adicionar_participantes', evento_id=evento_id))
                
                if file:
                    # Secure filename
                    filename = secure_filename(file.filename)
                    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    
                    try:
                        # Read file based on extension
                        if filename.endswith('.csv'):
                            df = pd.read_csv(filepath)
                        elif filename.endswith(('.xlsx', '.xls')):
                            df = pd.read_excel(filepath)
                        else:
                            flash('Formato de ficheiro não suportado.', 'error')
                            return redirect(url_for('main.adicionar_participantes', evento_id=evento_id))
                        
                        # Validate columns
                        if 'nome' not in df.columns or 'email' not in df.columns:
                            flash('Ficheiro deve conter colunas "nome" e "email".', 'error')
                            return redirect(url_for('main.adicionar_participantes', evento_id=evento_id))
                        
                        added_count = 0
                        for _, row in df.iterrows():
                            nome = row['nome']
                            email = row['email']
                            
                            # Check if participant already exists for this event
                            existing_participante = Participante.query.filter_by(
                                email=email, 
                                evento_id=evento_id
                            ).first()
                            
                            if not existing_participante:
                                # Create new participant for this event
                                novo_participante = Participante(
                                    nome=nome, 
                                    email=email, 
                                    evento_id=evento_id
                                )
                                db.session.add(novo_participante)
                                added_count += 1
                        
                        db.session.commit()
                        flash(f'{added_count} participante(s) importado(s) do ficheiro.', 'success')
                        return redirect(url_for('main.detalhe_evento', id=evento_id))
                    
                    except Exception as e:
                        logger.error(f"Error importing file: {str(e)}")
                        flash(f'Erro ao importar ficheiro: {str(e)}', 'error')
                    finally:
                        # Remove uploaded file
                        if os.path.exists(filepath):
                            os.remove(filepath)
            
            # Manual participant addition (original method)
            nome = request.form.get('nome')
            email = request.form.get('email')
            
            # Validate input
            if not nome or not email:
                flash('Nome e email são obrigatórios.', 'error')
                return redirect(url_for('main.adicionar_participantes', evento_id=evento_id))
            
            # Check if participant already exists for this event
            existing_participante = Participante.query.filter_by(
                email=email, 
                evento_id=evento_id
            ).first()
            
            if not existing_participante:
                # Create new participant for this event
                novo_participante = Participante(
                    nome=nome, 
                    email=email, 
                    evento_id=evento_id
                )
                db.session.add(novo_participante)
                db.session.commit()
                flash(f'Novo participante {nome} criado e adicionado ao evento.', 'success')
            else:
                flash(f'Participante {nome} já está no evento.', 'info')
            
            return redirect(url_for('main.detalhe_evento', id=evento_id))
        
        # GET request: show form to add participant
        return render_template('adicionar_participantes.html', evento=evento, utilizadores=utilizadores)
    
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemyError in adicionar_participantes: {str(e)}")
        db.session.rollback()
        flash(f'Erro ao adicionar participante: {str(e)}', 'error')
        return redirect(url_for('main.detalhe_evento', id=evento_id))
    except Exception as e:
        logger.error(f"Unexpected error in adicionar_participantes: {str(e)}")
        flash(f'Erro inesperado: {str(e)}', 'error')
        return redirect(url_for('main.detalhe_evento', id=evento_id))

@bp.route('/apagar_evento/<int:id>', methods=['POST'])
def apagar_evento(id):
    try:
        # Find the event
        evento = Evento.query.get_or_404(id)
        
        # Log details before deletion
        logger.info(f"Attempting to delete event: {evento.nome}")
        
        # Delete the event
        db.session.delete(evento)
        db.session.commit()
        
        # Log successful deletion
        logger.info(f"Event deleted successfully: {evento.nome}")
        
        flash('Evento apagado com sucesso!', 'success')
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemyError in apagar_evento: {str(e)}")
        db.session.rollback()
        flash(f'Erro ao apagar evento: {str(e)}', 'error')
    except Exception as e:
        logger.error(f"Unexpected error in apagar_evento: {str(e)}")
        flash(f'Erro inesperado: {str(e)}', 'error')
    
    return redirect(url_for('main.eventos'))

@bp.route('/criar_certificado/<int:evento_id>', methods=['GET', 'POST'])
def criar_certificado(evento_id):
    # Get base directory
    basedir = os.path.abspath(os.path.dirname(__file__))
    
    # Find the event
    evento = Evento.query.get_or_404(evento_id)
    
    # Find all participants for this event
    participantes = Participante.query.filter_by(evento_id=evento_id).all()
    
    # Default to first participant if exists
    primeiro_participante = participantes[0] if participantes else None

    if request.method == 'POST':
        certificar_todos = request.form.get('certificar_todos')

        try:
            # If "Certificar Todos" is checked
            if certificar_todos:
                certificados_gerados = 0
                certificados_ignorados = 0
                
                for participante in participantes:
                    # Detailed logging of participant status
                    logger.info(f"Checking participant: {participante.nome}")
                    logger.info(f"Participant status: {participante.status}")
                    logger.info(f"Current certificado_gerado status: {participante.certificado_gerado}")
                    
                    # Comprehensive check for certificate generation
                    if (participante.status == 'presente' and 
                        not participante.certificado_gerado):
                        
                        # Create PDF certificate
                        certificado_path = criar_certificado_pdf(
                            nome=participante.nome, 
                            titulo_evento=evento.nome, 
                            duracao=evento.duracao, 
                            data=evento.data, 
                            formadora=evento.formadora or 'Não definida',
                            basedir=basedir,
                            evento_id=evento.id,
                            participante_id=participante.id
                        )
                        
                        # Update participant record
                        participante.certificado_gerado = True
                        participante.certificado_enviado = False
                        
                        # Add to session and track
                        db.session.add(participante)
                        certificados_gerados += 1
                        
                        # Log successful certificate generation
                        logger.info(f"Certificate generated for {participante.nome}")
                    else:
                        # Log why a certificate was not generated
                        if participante.certificado_gerado:
                            logger.info(f"Skipping {participante.nome}: Certificate already generated")
                        elif participante.status != 'confirmado':
                            logger.info(f"Skipping {participante.nome}: Not marked as confirmed")
                        
                        certificados_ignorados += 1
                
                # Commit all changes
                db.session.commit()
                
                # Provide detailed feedback
                if certificados_gerados > 0:
                    flash(f'{certificados_gerados} certificados gerados com sucesso!', 'success')
                if certificados_ignorados > 0:
                    flash(f'{certificados_ignorados} participantes ignorados (já tinham certificado ou não estavam confirmados).', 'warning')
            
            # If generating for a single participant
            else:
                participante_id = request.form.get('participante_id')
                participante = Participante.query.get_or_404(participante_id)
                
                # Comprehensive check for single participant certificate
                if participante.status == 'confirmado' and not participante.certificado_gerado:
                    # Create PDF certificate
                    certificado_path = criar_certificado_pdf(
                        nome=participante.nome, 
                        titulo_evento=evento.nome, 
                        duracao=evento.duracao, 
                        data=evento.data, 
                        formadora=evento.formadora or 'Não definida',
                        basedir=basedir,
                        evento_id=evento.id,
                        participante_id=participante.id
                    )
                    
                    # Update participant record
                    participante.certificado_gerado = True
                    participante.certificado_enviado = False
                    
                    # Commit changes
                    db.session.add(participante)
                    db.session.commit()
                    
                    # Flash success message
                    flash(f'Certificado gerado para {participante.nome}', 'success')
                else:
                    # Provide specific feedback why certificate was not generated
                    if participante.certificado_gerado:
                        flash(f'Certificado para {participante.nome} já foi gerado', 'warning')
                    elif participante.status != 'confirmado':
                        flash(f'{participante.nome} não está marcado como confirmado', 'warning')
            
            # Redirect back to event details
            return redirect(url_for('main.detalhe_evento', id=evento_id))
        
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f'Erro ao gerar certificado: {str(e)}', 'error')
            return redirect(url_for('main.criar_certificado', evento_id=evento_id))

    # GET method: render the certificate generation page
    return render_template('criar_certificado.html', 
                           evento=evento, 
                           participantes=participantes,
                           certificado=primeiro_participante)

@bp.route('/remover_participante/<int:evento_id>/<int:participante_id>', methods=['POST'])
def remover_participante(evento_id, participante_id):
    try:
        # Find the event and participant
        evento = Evento.query.get_or_404(evento_id)
        participante = Participante.query.get_or_404(participante_id)
        
        # Check if participant is in the event
        if participante in evento.participantes:
            # Remove participant from event
            evento.participantes.remove(participante)
            db.session.commit()
            
            logger.info(f"Participant {participante.nome} removed from event {evento.nome}")
            flash(f'Participante {participante.nome} removido do evento.', 'success')
        else:
            flash(f'Participante {participante.nome} não está neste evento.', 'warning')
        
        return redirect(url_for('main.detalhe_evento', id=evento_id))
    
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemyError in remover_participante: {str(e)}")
        db.session.rollback()
        flash(f'Erro ao remover participante: {str(e)}', 'error')
        return redirect(url_for('main.detalhe_evento', id=evento_id))
    except Exception as e:
        logger.error(f"Unexpected error in remover_participante: {str(e)}")
        flash(f'Erro inesperado: {str(e)}', 'error')
        return redirect(url_for('main.detalhe_evento', id=evento_id))

@bp.route('/alterar_status_participante/<int:participante_id>', methods=['GET', 'POST'])
def alterar_status_participante(participante_id):
    try:
        # Find the participant
        participante = Participante.query.get_or_404(participante_id)
        
        # Determine if this is an AJAX request
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        # Get the new status from request
        if request.method == 'GET':
            new_status = request.args.get('status', participante.status)
        else:
            new_status = request.form.get('status', participante.status)
        
        # Validate status
        valid_statuses = ['pendente', 'confirmado', 'presente', 'cancelado']
        if new_status not in valid_statuses:
            raise ValueError(f"Invalid status: {new_status}")
        
        # Update status
        participante.status = new_status
        
        # Commit changes
        db.session.commit()
        
        # Prepare response
        if is_ajax:
            return jsonify({
                'status': 'success', 
                'message': f'Status atualizado para {new_status}',
                'participante_id': participante_id,
                'new_status': new_status
            }), 200
        
        # Fallback for non-AJAX requests
        flash(f'Status do participante {participante.nome} atualizado para {participante.status}.', 'success')
        return redirect(url_for('main.detalhe_evento', id=participante.evento_id))
    
    except SQLAlchemyError as e:
        # Rollback the session
        db.session.rollback()
        
        # Log the error
        logger.error(f"SQLAlchemyError in alterar_status_participante: {str(e)}")
        
        # Prepare error response
        if is_ajax:
            return jsonify({
                'status': 'error', 
                'message': f'Erro ao atualizar status: {str(e)}'
            }), 400
        
        # Fallback for non-AJAX requests
        flash(f'Erro ao alterar status do participante: {str(e)}', 'error')
        return redirect(url_for('main.detalhe_evento', id=participante.evento_id))
    
    except Exception as e:
        # Log unexpected errors
        logger.error(f"Unexpected error in alterar_status_participante: {str(e)}")
        
        # Prepare error response
        if is_ajax:
            return jsonify({
                'status': 'error', 
                'message': f'Erro inesperado: {str(e)}'
            }), 500
        
        # Fallback for non-AJAX requests
        flash(f'Erro inesperado: {str(e)}', 'error')
        return redirect(url_for('main.detalhe_evento', id=participante.evento_id))

@bp.route('/alterar_status_evento/<int:evento_id>', methods=['POST'])
def alterar_status_evento(evento_id):
    try:
        # Find the event
        evento = Evento.query.get_or_404(evento_id)
        
        # Get the new status and action type
        action = request.form.get('action')
        
        # Get all participants for this event
        participantes = Participante.query.filter_by(evento_id=evento_id).all()
        
        # Bulk status change
        if action == 'todos_pendentes':
            for participante in participantes:
                participante.status = 'pendente'
            message = 'Todos os participantes definidos como pendentes.'
        
        elif action == 'todos_confirmados':
            for participante in participantes:
                participante.status = 'confirmado'
            message = 'Todos os participantes confirmados.'
        
        elif action == 'todos_cancelados':
            for participante in participantes:
                participante.status = 'cancelado'
            message = 'Todos os participantes cancelados.'
        
        elif action == 'todos_presentes':
            for participante in participantes:
                participante.status = 'presente'
            message = 'Todos os participantes marcados como presentes.'
        
        else:
            flash('Ação inválida.', 'error')
            return redirect(url_for('main.detalhe_evento', id=evento_id))
        
        # Commit changes
        db.session.commit()
        
        # Redirect back to the event details
        flash(message, 'success')
        return redirect(url_for('main.detalhe_evento', id=evento_id))
    
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemyError in alterar_status_evento: {str(e)}")
        db.session.rollback()
        flash(f'Erro ao alterar status dos participantes: {str(e)}', 'error')
        return redirect(url_for('main.detalhe_evento', id=evento_id))
    except Exception as e:
        logger.error(f"Unexpected error in alterar_status_evento: {str(e)}")
        flash(f'Erro inesperado: {str(e)}', 'error')
        return redirect(url_for('main.detalhe_evento', id=evento_id))

@bp.route('/criar_evento_teste')
def criar_evento_teste():
    """
    Create a sample event for testing purposes
    """
    try:
        from datetime import date, timedelta
        
        # Check if any events exist
        existing_eventos = Evento.query.all()
        if existing_eventos:
            logger.info(f"Already have {len(existing_eventos)} eventos. No need to create test event.")
            return redirect(url_for('main.eventos'))
        
        # Create a sample event
        novo_evento = Evento(
            nome='Evento de Teste',
            data=date.today() + timedelta(days=30),
            duracao=2,
            formadora='Administrador'
        )
        
        db.session.add(novo_evento)
        db.session.commit()
        
        logger.info("Criado evento de teste com sucesso!")
        flash('Evento de teste criado com sucesso!', 'success')
        return redirect(url_for('main.eventos'))
    
    except Exception as e:
        logger.error(f"Erro ao criar evento de teste: {e}")
        flash(f'Erro ao criar evento de teste: {e}', 'error')
        return redirect(url_for('main.index'))

@bp.route('/visualizar_certificado/<int:participante_id>')
def visualizar_certificado(participante_id):
    try:
        # Find the participant
        participante = Participante.query.get_or_404(participante_id)
        evento = participante.evento
        
        # Log detailed information for debugging
        logger.info(f"Visualizing certificate for participant {participante.nome}")
        logger.info(f"Certificado gerado: {participante.certificado_gerado}")
        
        # Check if certificate has been generated
        if not participante.certificado_gerado:
            logger.warning(f"Certificate not generated for participant {participante.nome}")
            flash('Certificado ainda não foi gerado para este participante.', 'error')
            return redirect(url_for('main.detalhe_evento', id=evento.id))
        
        # Construct the path to the certificate
        basedir = os.path.abspath(os.path.dirname(__file__))
        certificado_path = os.path.join(basedir, 'uploads', 'certificados', 
                                        f'certificado_{evento.id}_{participante.id}.pdf')
        
        # Log the certificate path for debugging
        logger.info(f"Certificate path: {certificado_path}")
        
        # Check if certificate file exists
        if not os.path.exists(certificado_path):
            logger.error(f"Certificate file not found: {certificado_path}")
            flash('Arquivo do certificado não encontrado.', 'error')
            return redirect(url_for('main.detalhe_evento', id=evento.id))
        
        # Send the file
        return send_file(certificado_path, 
                         mimetype='application/pdf', 
                         download_name=f'Certificado_{participante.nome}.pdf',
                         as_attachment=False)
    
    except Exception as e:
        # Log the full error for debugging
        logger.error(f"Error viewing certificate: {str(e)}", exc_info=True)
        flash('Erro ao visualizar o certificado.', 'error')
        return redirect(url_for('main.eventos'))

@bp.route('/enviar_certificado_email/<int:participante_id>', methods=['POST'])
def enviar_certificado_email(participante_id):
    try:
        # Find the participant
        participante = Participante.query.get_or_404(participante_id)
        evento = participante.evento

        # Check if participant was present
        if participante.status != 'presente':
            flash('Apenas participantes presentes podem receber certificados.', 'warning')
            return redirect(url_for('main.detalhe_evento', id=evento.id))

        # Generate certificate
        basedir = current_app.config['BASE_DIR']
        certificado_path = criar_certificado_pdf(
            nome=participante.nome, 
            titulo_evento=evento.nome, 
            duracao=evento.duracao, 
            data=evento.data, 
            formadora=evento.formadora,
            basedir=basedir,
            participante_id=participante.id,
            evento_id=evento.id
        )

        # Send email with certificate
        msg = MIMEMultipart()
        msg['From'] = current_app.config['EMAIL_USER']
        msg['To'] = participante.email
        msg['Subject'] = f'Certificado - {evento.nome}'

        # Email body
        body = f"""Olá {participante.nome},

Segue em anexo o seu certificado de participação no evento {evento.nome}.

Detalhes do Evento:
- Título: {evento.nome}
- Data: {evento.data.strftime('%d/%m/%Y')}
- Duração: {evento.duracao} minutos
- Formadora: {evento.formadora}

Obrigado por participar!

Cumprimentos,
Equipa de Eventos
"""
        msg.attach(MIMEText(body, 'plain'))

        # Attach certificate
        with open(certificado_path, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename="certificado_{participante.nome}.pdf"')
            msg.attach(part)

        # Send email
        with smtplib.SMTP(current_app.config['SMTP_SERVER'], current_app.config['SMTP_PORT']) as server:
            server.starttls()
            server.login(current_app.config['EMAIL_USER'], current_app.config['EMAIL_PASSWORD'])
            server.send_message(msg)

        # Mark as certificate sent
        participante.certificado_enviado = True
        db.session.commit()

        flash(f'Certificado enviado com sucesso para {participante.email}', 'success')
    except Exception as e:
        logger.error(f"Erro no envio de certificado: {str(e)}")
        flash(f'Erro inesperado: {str(e)}', 'error')

    return redirect(url_for('main.detalhe_evento', id=evento.id))

@bp.route('/enviar_certificados_evento/<int:evento_id>', methods=['POST'])
def enviar_certificados_evento(evento_id):
    try:
        # Find the event
        evento = Evento.query.get_or_404(evento_id)

        # Find all present participants
        participantes_presentes = Participante.query.filter_by(
            evento_id=evento_id, 
            status='presente'
        ).all()

        # Track successful and failed emails
        emails_enviados = 0
        emails_falhos = 0

        # Send certificates to all present participants
        for participante in participantes_presentes:
            try:
                # Generate certificate
                basedir = current_app.config['BASE_DIR']
                certificado_path = criar_certificado_pdf(
                    nome=participante.nome, 
                    titulo_evento=evento.nome, 
                    duracao=evento.duracao, 
                    data=evento.data, 
                    formadora=evento.formadora,
                    basedir=basedir,
                    participante_id=participante.id,
                    evento_id=evento.id
                )

                # Send email
                msg = MIMEMultipart()
                msg['From'] = current_app.config['EMAIL_USER']
                msg['To'] = participante.email
                msg['Subject'] = f'Certificado - {evento.nome}'

                # Email body
                body = f"""Olá {participante.nome},

Segue em anexo o seu certificado de participação no evento {evento.nome}.

Detalhes do Evento:
- Título: {evento.nome}
- Data: {evento.data.strftime('%d/%m/%Y')}
- Duração: {evento.duracao} minutos
- Formadora: {evento.formadora}

Obrigado por participar!

Cumprimentos,
Equipa de Eventos
"""
                msg.attach(MIMEText(body, 'plain'))

                # Attach certificate
                with open(certificado_path, 'rb') as f:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', f'attachment; filename="certificado_{participante.nome}.pdf"')
                    msg.attach(part)

                # Send email
                with smtplib.SMTP(current_app.config['SMTP_SERVER'], current_app.config['SMTP_PORT']) as server:
                    server.starttls()
                    server.login(current_app.config['EMAIL_USER'], current_app.config['EMAIL_PASSWORD'])
                    server.send_message(msg)

                # Mark as certificate sent
                participante.certificado_enviado = True
                emails_enviados += 1

            except Exception as email_error:
                logger.error(f"Erro ao enviar certificado para {participante.nome}: {str(email_error)}")
                emails_falhos += 1

        # Commit changes
        db.session.commit()

        # Flash summary
        flash(f'Certificados enviados: {emails_enviados}. Falhas: {emails_falhos}', 'info')

    except Exception as e:
        logger.error(f"Erro no envio de certificados em massa: {str(e)}")
        flash(f'Erro inesperado: {str(e)}', 'error')

    return redirect(url_for('main.detalhe_evento', id=evento_id))

import os
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders