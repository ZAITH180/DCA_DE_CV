from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import pymysql

app = Flask(__name__)
app.secret_key = 'super_secret_key_dca'

# --- CONFIGURACIÓN DE LA BASE DE DATOS ---
# Nos conectamos directamente a la base de datos que acabamos de crear
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/dca_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- MODELO DE USUARIO ---
# El nombre de la tabla y las columnas coinciden EXACTAMENTE con el SQL que ejecutamos
class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

with app.app_context():
    db.create_all() # Esto no hará nada porque ya existen, pero es buena práctica

# --- RUTAS ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/denuncia')
def denuncia():
    return render_template('denuncia.html')

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
            flash("Este correo ya está registrado. Intenta iniciar sesión.", "error")
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
            return f"¡Bienvenido {usuario.username}! Has iniciado sesión correctamente. <a href='/'>Volver al inicio</a>"
        else:
            flash("Correo o contraseña incorrectos.", "error")
            return redirect(url_for('login'))
            
    return render_template('login.html')

if __name__ == '__main__':
    app.run(debug=True)