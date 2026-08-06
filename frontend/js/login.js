/* Envia o login via fetch pra API (POST /api/login) em vez de um POST de
   formulário normal — assim a página não recarrega e dá pra mostrar o erro
   (ex: "Email ou senha inválidos") direto na tela, sem depender do Flask
   re-renderizar nada. */

const form = document.getElementById("loginForm");
const mensagem = document.getElementById("mensagem");

function mostrarErro(texto) {
    mensagem.textContent = texto;
    mensagem.className = "mensagem mensagem-erro";
}

form.addEventListener("submit", async (evento) => {
    evento.preventDefault();

    const resposta = await fetch("/api/login", {
        method: "POST",
        body: new FormData(form),
    });
    const dados = await resposta.json();

    if (!dados.ok) {
        mostrarErro(dados.erro);
        return;
    }

    window.location.href = dados.redirect;
});
