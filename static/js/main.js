function mostrarAlerta() {
    const alerta = document.getElementById('alerta-personalizada');
    alerta.classList.add('mostrar');

    // Ocultar la alerta después de 3.5 segundos
    setTimeout(() => {
        alerta.classList.remove('mostrar');
    }, 3500);
}

function verificarTerminos() {
    const termsCheckbox = document.getElementById('terms');
    
    if (termsCheckbox && !termsCheckbox.checked) {
        mostrarAlerta(); // Llamamos a nuestra alerta personalizada
        return false;
    }
    return true;
}

function continuarAnonimo() {
    if (verificarTerminos()) {
        window.location.href = '/anonimo';
    }
}

function continuarCorreo() {
    if (verificarTerminos()) {
        window.location.href = '/login';
    }
}