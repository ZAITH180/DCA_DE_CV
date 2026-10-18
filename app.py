from flask import Flask, render_template, send_from_directory, request

app = Flask(__name__)

@app.route('/js/<path:filename>')
def serve_js(filename):
    return send_from_directory('js', filename)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/denuncia')
def denuncia():
    return render_template('denuncia.html')

@app.route('/exito', methods=['GET', 'POST'])
def exito():
    return render_template('exito.html')

@app.route('/muro')
def muro():
    return render_template('muro.html')

@app.route('/perfil')
def perfil():
    return render_template('perfil.html')

@app.route('/notificaciones')
def notificaciones():
    return render_template('notificaciones.html')

if __name__ == '__main__':
    app.run(debug=True)