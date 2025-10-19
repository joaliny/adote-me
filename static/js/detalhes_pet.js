// static/js/detalhes_pet.js

// Modal de Login/Cadastro
function abrirModalLogin() {
    document.getElementById('modal-login').style.display = 'block';
}

function fecharModalLogin() {
    document.getElementById('modal-login').style.display = 'none';
}

// Modal de Confirmação
function abrirModal() {
    document.getElementById('modal-confirmacao').style.display = 'block';
}

function fecharModal() {
    document.getElementById('modal-confirmacao').style.display = 'none';
}

// Fechar modais ao clicar fora
window.onclick = function (event) {
    const modalLogin = document.getElementById('modal-login');
    const modalConfirmacao = document.getElementById('modal-confirmacao');

    if (event.target === modalLogin) {
        modalLogin.style.display = 'none';
    }
    if (event.target === modalConfirmacao) {
        modalConfirmacao.style.display = 'none';
    }
}

// Auto-abrir modais quando a página carrega
document.addEventListener('DOMContentLoaded', function () {
    // Verificar URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    const mostrarModalLogin = urlParams.get('mostrar_modal_login');
    const sucesso = urlParams.get('sucesso');

    if (mostrarModalLogin === 'true') {
        abrirModalLogin();
    }

    if (sucesso === 'true') {
        abrirModal();
    }
});