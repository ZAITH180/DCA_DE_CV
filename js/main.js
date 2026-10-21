document.addEventListener("DOMContentLoaded", function() {
    // Seleccionar todos los botones dentro de la barra de filtros del muro
    const botonesFiltro = document.querySelectorAll("main div div button");

    botonesFiltro.forEach(boton => {
        const texto = boton.textContent.trim().toLowerCase();
        
        boton.addEventListener("click", function() {
            let filtro = 'en_proceso';
            if (texto.includes('todos')) filtro = 'todos';
            else if (texto.includes('recientes')) filtro = 'recientes';
            else if (texto.includes('proceso')) filtro = 'en_proceso';
            else if (texto.includes('cerradas')) filtro = 'cerradas';

            // Redirigir a la ruta del muro con el filtro seleccionado
            window.location.href = `/muro?filtro=${filtro}`;
        });
    });
});