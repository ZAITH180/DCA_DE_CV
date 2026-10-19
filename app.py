from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
import pymysql
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_super_segura'

# Configuración de la base de datos con PyMySQL (XAMPP)
def get_db_connection():
    connection = pymysql.connect(
        host='localhost',
        user='root',
        password='',
        database='dca_db',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
    return connection

# Ruta Auxiliar para servir los scripts JS referenciados como url_for('serve_js', filename='...')
@app.route('/js/<path:filename>')
def serve_js(filename):
    return send_from_directory(os.path.join(app.root_path, 'static', 'js'), filename)

# Ruta Principal / Login inicial
@app.route('/')
def index():
    return render_template('login.html')

# 1. REGISTRO (Adaptado a register.html)
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
                user = cursor.fetchone()
                
                if user:
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

# 2. INICIO DE SESIÓN (Adaptado a login.html)
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

# 3. RECUPERAR CONTRASEÑA (Adaptado a recuperar_pass.html)
@app.route('/recuperar', methods=['GET', 'POST'])
def recuperar():
    if request.method == 'POST' or request.method == 'GET':
        correo = request.args.get('email') or request.form.get('email')
        
        if correo:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM usuarios WHERE correo = %s", (correo,))
                user = cursor.fetchone()
            conn.close()
            
            if user:
                session['correo_recuperacion'] = correo
                return redirect(url_for('verificar_codigo'))
            else:
                flash('El correo no se encuentra registrado.', 'danger')
                
    return render_template('recuperar_pass.html')

# 4. VERIFICAR CÓDIGO
@app.route('/verificar-codigo')
def verificar_codigo():
    return render_template('verificar_codigo.html')

# 5. CAMBIAR CONTRASEÑA (Adaptado a cambiar_pass.html)
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
                cursor.execute("UPDATE usuarios SET password = %s WHERE correo = %s", (hashed_password, correo))
                conn.commit()
            conn.close()
            
            session.pop('correo_recuperacion', None)
            flash('Contraseña actualizada con éxito.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Sesión de recuperación expirada o correo no válido.', 'danger')
            return redirect(url_for('recuperar'))
            
    return render_template('cambiar_pass.html')

# 6. RUTAS SECUNDARIAS DE LA APLICACIÓN
@app.route('/muro')
def muro():
    return render_template('muro.html')

@app.route('/notificaciones')
def notificaciones():
    return render_template('notificaciones.html')

@app.route('/perfil')
def perfil():
    return render_template('perfil.html')

@app.route('/configuracion')
def configuracion():
    return render_template('configuracion.html')

@app.route('/denuncia')
def denuncia():
    return render_template('denuncia.html')

@app.route('/exito')
def exito():
    return render_template('exito.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)