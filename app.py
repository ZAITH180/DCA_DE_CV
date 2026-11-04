import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import pymysql

app = Flask(__name__)
app.secret_key = 'super_secret_key_dca'

# --- CONFIGURACIÓN DE SUBIDA DE ARCHIVOS ---
UPLOAD_FOLDER = os.path.join('static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# Asegurarnos de que la carpeta exista
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- CONFIGURACIÓN DE LA BASE DE DATOS ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/dca_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- MODELOS ---
class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

class Denuncia(db.Model):
    __tablename__ = 'denuncias'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    categoria = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    ruta_imagen = db.Column(db.String(255), nullable=True) # Nuevo campo
    latitud = db.Column(db.String(50), nullable=True)      # Nuevo campo
    longitud = db.Column(db.String(50), nullable=True)     # Nuevo campo
    fecha = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())

with app.app_context():
    db.create_all()

# --- RUTAS ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/muro')
def muro():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    denuncias_usuario = Denuncia.query.filter_by(usuario_id=session['usuario_id']).order_by(Denuncia.fecha.desc()).all()
    return render_template('muro.html', nombre=session['usuario_nombre'], denuncias=denuncias_usuario)

@app.route('/denuncia')
def denuncia():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    return render_template('denuncia.html')

# --- RUTA PARA GUARDAR LA DENUNCIA CON IMAGEN Y UBICACIÓN ---
@app.route('/publicar_denuncia', methods=['POST'])
def publicar_denuncia():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    categoria = request.form.get('categoria')
    descripcion = request.form.get('descripcion')
    latitud = request.form.get('latitud')
    longitud = request.form.get('longitud')
    foto = request.files.get('foto') # Recibimos el archivo
    
    if not categoria or not descripcion:
        flash("Por favor, llene los campos de texto.", "error")
        return redirect(url_for('denuncia'))

    # Guardar la imagen si el usuario subió una
    ruta_guardada = None
    if foto and foto.filename != '':
        # Limpiamos el nombre del archivo por seguridad
        filename = secure_filename(foto.filename)
        # Lo guardamos en static/uploads/
        foto.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        ruta_guardada = filename # Solo guardamos el nombre en la BD

    nueva_denuncia = Denuncia(
        usuario_id=session['usuario_id'],
        categoria=categoria,
        descripcion=descripcion,
        ruta_imagen=ruta_guardada,
        latitud=latitud,
        longitud=longitud
    )
    
    try:
        db.session.add(nueva_denuncia)
        db.session.commit()
        flash("¡Denuncia publicada exitosamente!", "success")
        return redirect(url_for('muro'))
    except Exception as e:
        db.session.rollback()
        flash(f"Error al publicar: {str(e)}", "error")
        return redirect(url_for('denuncia'))

# --- REGISTRO, LOGIN Y LOGOUT ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash("Las contraseñas no coinciden.", "error")
            return redirect(url_for('register'))
            
        usuario_existente = Usuario.query.filter_by(email=email).first()
        if usuario_existente:
            flash("Este correo ya está registrado.", "error")
            return redirect(url_for('login'))
            
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        nuevo_usuario = Usuario(username=username, email=email, password=hashed_password)
        
        try:
            db.session.add(nuevo_usuario)
            db.session.commit()
            flash("¡Registro exitoso! Ahora puedes iniciar sesión.", "success")
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error al registrar: {str(e)}", "error")
            return redirect(url_for('register'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        usuario = Usuario.query.filter_by(email=email).first()
        
        if usuario and check_password_hash(usuario.password, password):
            session['usuario_id'] = usuario.id
            session['usuario_nombre'] = usuario.username
            return redirect(url_for('muro'))
        else:
            flash("Correo o contraseña incorrectos.", "error")
            return redirect(url_for('login'))
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# --- RUTAS DE PLACEHOLDER (Para que el muro no falle) ---
@app.route('/notificaciones')
def notificaciones():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    # Por ahora redirigimos al muro
    return redirect(url_for('muro')) 

@app.route('/perfil')
def perfil():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    # Por ahora redirigimos al muro
    return redirect(url_for('muro'))

if __name__ == '__main__':
    app.run(debug=True)