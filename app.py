from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
import pymysql
import random
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_super_segura'

# Carpeta para archivos multimedia subidos
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Configuración de la base de datos con PyMySQL (XAMPP)
def get_db_connection():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='',
        database='dca_db',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

# Servir scripts JS
@app.route('/js/<path:filename>')
def serve_js(filename):
    return send_from_directory(os.path.join(app.root_path, 'static', 'js'), filename)

# Ruta Principal / Login
@app.route('/')
def index():
    return render_template('login.html')

# 1. REGISTRO
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nombre = request.form.get('username')
        correo = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Las contraseñas no coinciden.', 'danger')
            return redirect(url_for('register'))
        
        hashed_password = generate_password_hash(password)
        
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM usuarios WHERE correo = %s", (correo,))
                if cursor.fetchone():
                    flash('El correo ya está registrado.', 'danger')
                    return redirect(url_for('register'))
                
                cursor.execute("INSERT INTO usuarios (nombre, correo, password) VALUES (%s, %s, %s)", 
                            (nombre, correo, hashed_password))
                conn.commit()
            conn.close()
            
            flash('Registro exitoso. Ahora puedes iniciar sesión.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash(f'Error en la base de datos: {e}', 'danger')
            return redirect(url_for('register'))
        
    return render_template('register.html')

# 2. INICIO DE SESIÓN
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        correo = request.form.get('email')
        password = request.form.get('password')
        
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM usuarios WHERE correo = %s", (correo,))
            user = cursor.fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['user_name'] = user['nombre']
            session['user_email'] = user['correo']
            return redirect(url_for('muro'))
        else:
            flash('Correo o contraseña incorrectos.', 'danger')
            
    return render_template('login.html')

# 3. RECUPERAR CONTRASEÑA
@app.route('/recuperar', methods=['GET', 'POST'])
def recuperar():
    if request.method == 'POST' or request.method == 'GET':
        correo = request.args.get('email') or request.form.get('email')
        if correo:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM usuarios WHERE correo = %s", (correo,))
                user = cursor.fetchone()
            
            if user:
                codigo_aleatorio = str(random.randint(100000, 999999))
                with conn.cursor() as cursor:
                    cursor.execute("UPDATE usuarios SET codigo_recuperacion = %s WHERE correo = %s", (codigo_aleatorio, correo))
                    conn.commit()
                conn.close()
                
                print(f"\n [CÓDIGO DE RECUPERACIÓN]: {codigo_aleatorio} para {correo}\n")
                session['correo_recuperacion'] = correo
                return redirect(url_for('verificar_codigo'))
            else:
                conn.close()
                flash('El correo no se encuentra registrado.', 'danger')
                
    return render_template('recuperar_pass.html')

@app.route('/verificar-codigo', methods=['GET', 'POST'])
def verificar_codigo():
    if request.method == 'POST':
        codigo_ingresado = request.form.get('codigo')
        correo = session.get('correo_recuperacion')
        
        if correo:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT codigo_recuperacion FROM usuarios WHERE correo = %s", (correo,))
                resultado = cursor.fetchone()
            conn.close()
            
            if resultado and resultado['codigo_recuperacion'] == codigo_ingresado:
                return redirect(url_for('cambiar_pass'))
            else:
                flash('Código incorrecto.', 'danger')
        else:
            return redirect(url_for('recuperar'))
            
    return render_template('verificar_codigo.html')

@app.route('/cambiar-pass', methods=['GET', 'POST'])
def cambiar_pass():
    if request.method == 'POST':
        nueva_password = request.form.get('new-password')
        confirm_password = request.form.get('confirm-password')
        
        if nueva_password != confirm_password:
            flash('Las contraseñas no coinciden.', 'danger')
            return redirect(url_for('cambiar_pass'))
            
        correo = session.get('correo_recuperacion')
        if correo:
            hashed_password = generate_password_hash(nueva_password)
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("UPDATE usuarios SET password = %s, codigo_recuperacion = NULL WHERE correo = %s", (hashed_password, correo))
                conn.commit()
            conn.close()
            session.pop('correo_recuperacion', None)
            return redirect(url_for('login'))
            
    return render_template('cambiar_pass.html')

# 4. MURO (Con soporte para filtros: Todos, Recientes, En proceso, Cerradas)
@app.route('/muro')
def muro():
    filtro = request.args.get('filtro', 'en_proceso') # Por defecto muestra 'En proceso'
    
    conn = get_db_connection()
    with conn.cursor() as cursor:
        if filtro == 'todos':
            cursor.execute("SELECT * FROM denuncias ORDER BY id DESC")
        elif filtro == 'recientes':
            cursor.execute("SELECT * FROM denuncias ORDER BY fecha DESC LIMIT 5")
        elif filtro == 'cerradas':
            cursor.execute("SELECT * FROM denuncias WHERE estado = 'Cerrada' ORDER BY id DESC")
        else: # 'en_proceso'
            cursor.execute("SELECT * FROM denuncias WHERE estado = 'En proceso' ORDER BY id DESC")
            
        denuncias = cursor.fetchall()
    conn.close()
    
    return render_template('muro.html', denuncias=denuncias, filtro_actual=filtro)
# 5. VER PÁGINA DE PUBLICACIÓN DE DENUNCIA
@app.route('/denuncia')
def denuncia():
    return render_template('denuncia.html')

# 6. REGISTRAR DENUNCIA (Ruta 'exito' ejecutada al presionar Publicar)
@app.route('/exito', methods=['GET', 'POST'])
def exito():
    if request.method == 'POST':
        usuario_id = session.get('user_id')
        
        # Extracción de campos enviados desde el formulario (se captura cualquier name o valor por defecto)
        categoria = request.form.get('categoria') or request.form.get('tipo_denuncia') or 'General'
        descripcion = request.form.get('descripcion') or request.form.get('detalles') or 'Sin descripción proporcionada'
        ubicacion = request.form.get('ubicacion') or request.form.get('mapa') or 'Ubicación no especificada'
        
        # Manejo de archivo subido (Foto o Video)
        filename = None
        file = request.files.get('multimedia') or request.files.get('archivo')
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        # Guardado en base de datos
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO denuncias (usuario_id, categoria, descripcion, multimedia, ubicacion, estado) 
                VALUES (%s, %s, %s, %s, %s, 'En proceso')
            """, (usuario_id, categoria, descripcion, filename, ubicacion))
            conn.commit()
        conn.close()
        
    return render_template('exito.html')

# Rutas secundarias
@app.route('/notificaciones')
def notificaciones():
    return render_template('notificaciones.html')

@app.route('/perfil')
def perfil():
    return render_template('perfil.html')

@app.route('/configuracion')
def configuracion():
    return render_template('configuracion.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)