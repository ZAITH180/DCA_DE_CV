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
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True) # Ahora permite nulos
    categoria = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    ruta_imagen = db.Column(db.String(255), nullable=True)
    latitud = db.Column(db.String(50), nullable=True)
    longitud = db.Column(db.String(50), nullable=True)
    estado = db.Column(db.String(50), default='Reciente')
    fecha = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())

with app.app_context():
    db.create_all()

# --- RUTAS ---

@app.route('/')
def index():
    return render_template('index.html')

# --- NUEVA RUTA: ACCESO ANÓNIMO ---
@app.route('/anonimo')
def anonimo():
    # Marcamos en la sesión que este usuario es anónimo
    session['anonimo'] = True
    return redirect(url_for('muro_anonimo'))

# --- NUEVA RUTA: MURO ANÓNIMO ---
@app.route('/muro_anonimo')
def muro_anonimo():
    # Solo se puede acceder si se marcó como anónimo
    if not session.get('anonimo'):
        return redirect(url_for('index'))
    
    # Traemos TODAS las denuncias anónimas (donde usuario_id es NULL)
    denuncias_anonimas = Denuncia.query.filter_by(usuario_id=None).order_by(Denuncia.fecha.desc()).all()
    
    return render_template('muro_anonimo.html', denuncias=denuncias_anonimas)

@app.route('/muro')
def muro():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    filtro = request.args.get('filtro', 'Todos')
    query = Denuncia.query.filter_by(usuario_id=session['usuario_id'])
    
    if filtro == 'Recientes':
        query = query.filter_by(estado='Reciente')
    elif filtro == 'En Proceso':
        query = query.filter_by(estado='En Proceso')
    elif filtro == 'Cerradas':
        query = query.filter_by(estado='Cerrada')
    
    denuncias_usuario = query.order_by(Denuncia.fecha.desc()).all()
    
    # Contar notificaciones (denuncias que no están 'Reciente')
    cantidad_notificaciones = Denuncia.query.filter(
        Denuncia.usuario_id == session['usuario_id'],
        Denuncia.estado != 'Reciente'
    ).count()
    
    return render_template('muro.html', 
                           nombre=session['usuario_nombre'], 
                           denuncias=denuncias_usuario, 
                           filtro_activo=filtro,
                           cantidad_notificaciones=cantidad_notificaciones)  
# --- FORMULARIO DE DENUNCIA (Aplica para ambos) ---
@app.route('/denuncia')
def denuncia():
    if 'usuario_id' not in session and not session.get('anonimo'):
        return redirect(url_for('index'))
    return render_template('denuncia.html')

# --- GUARDAR DENUNCIA (Modificado) ---
@app.route('/publicar_denuncia', methods=['POST'])
def publicar_denuncia():
    # Verificamos si hay sesión (normal o anónima)
    if 'usuario_id' not in session and not session.get('anonimo'):
        return redirect(url_for('index'))
    
    categoria = request.form.get('categoria')
    descripcion = request.form.get('descripcion')
    latitud = request.form.get('latitud')
    longitud = request.form.get('longitud')
    foto = request.files.get('foto')
    
    if not categoria or not descripcion:
        flash("Por favor, llene los campos de texto.", "error")
        return redirect(url_for('denuncia'))

    ruta_guardada = None
    if foto and foto.filename != '':
        filename = secure_filename(foto.filename)
        foto.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        ruta_guardada = filename

    # Si está logueado usa su ID, si es anónimo se queda en None
    id_usuario = session.get('usuario_id', None)

    nueva_denuncia = Denuncia(
        usuario_id=id_usuario,
        categoria=categoria,
        descripcion=descripcion,
        ruta_imagen=ruta_guardada,
        latitud=latitud,
        longitud=longitud,
        estado='Reciente'
    )
    
    try:
        db.session.add(nueva_denuncia)
        db.session.commit()
        return redirect(url_for('exito'))
    except Exception as e:
        db.session.rollback()
        flash(f"Error al publicar: {str(e)}", "error")
        return redirect(url_for('denuncia'))

@app.route('/exito')
def exito():
    if 'usuario_id' not in session and not session.get('anonimo'):
        return redirect(url_for('index'))
    return render_template('exito.html')

# --- REGISTRO, LOGIN Y LOGOUT (Igual que antes) ---
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
            session.clear() # Limpiamos cualquier sesión anónima previa
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

# --- RUTAS DE NOTIFICACIONES Y PERFIL ---
@app.route('/notificaciones')
def notificaciones():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    denuncias_actualizadas = Denuncia.query.filter(
        Denuncia.usuario_id == session['usuario_id'],
        Denuncia.estado != 'Reciente'
    ).order_by(Denuncia.fecha.desc()).all()
    
    return render_template('notificaciones.html', notificaciones=denuncias_actualizadas)

@app.route('/perfil')
def perfil():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    usuario = Usuario.query.get(session['usuario_id'])
    return render_template('perfil.html', usuario=usuario)

@app.route('/terminos')
def terminos():
    return render_template('terminos.html')

@app.route('/configuracion')
def configuracion():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    return render_template('configuracion.html')

# --- RUTA PARA VER EL DETALLE DE UNA DENUNCIA ---
@app.route('/denuncia/<int:id>')
def ver_denuncia(id):
    # Verificamos que esté logueado o en modo anónimo
    if 'usuario_id' not in session and not session.get('anonimo'):
        return redirect(url_for('index'))
    
    # Buscamos la denuncia por su ID
    denuncia = Denuncia.query.get_or_404(id)
    
    return render_template('detalle_denuncia.html', d=denuncia)

if __name__ == '__main__':
    app.run(debug=True)