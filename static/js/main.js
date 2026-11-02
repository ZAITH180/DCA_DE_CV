function verificarTerminos() {
    const termsCheckbox = document.getElementById('terms');
    
    
    if (termsCheckbox && !termsCheckbox.checked) {
        termsCheckbox.checked = true; 
    }
    return true;
}

function continuarAnonimo() {
    if (verificarTerminos()) {
        window.location.href = '/denuncia';
    }
}

function continuarCorreo() {
    if (verificarTerminos()) {
      
        window.location.href = '/login';
    }
}