function verificarTerminos() {
    const termsCheckbox = document.getElementById('terms');
    if (!termsCheckbox.checked) {
        alert("Por favor, acepta los términos y condiciones para continuar.");
        return false;
    }
    return true;
}

function continuarAnonimo() {
    if (verificarTerminos()) {
        // Redirección añadida a la vista de reporte anónimo
        window.location.href = '/denuncia';
    }
}

function continuarCorreo() {
    if (verificarTerminos()) {
        // Redirige a la pantalla de login
        window.location.href = '/login';
    }
}