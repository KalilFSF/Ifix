/* Envia o login via fetch pra API (POST /api/login) em vez de um POST de
   formulário normal — assim a página não recarrega e dá pra mostrar o erro
   (ex: "Email ou senha inválidos") direto na tela, sem depender do Flask
   re-renderizar nada. */

const formLogin = document.getElementById("loginForm");

formLogin.addEventListener("submit", async (evento) => {
    evento.preventDefault();

    const botao = formLogin.querySelector("button[type=submit]");
    const textoOriginal = botao.textContent;
    botao.disabled = true;
    botao.textContent = "Entrando...";
    limparMensagem();

    // requisitar() não lança: uma API fora do ar volta como {ok:false} com
    // mensagem pronta, em vez de deixar o botão travado em "Entrando...".
    const resultado = await enviarFormulario("/api/login", new FormData(formLogin));

    botao.disabled = false;
    botao.textContent = textoOriginal;

    if (!resultado.ok) {
        mostrarErro(resultado.erro);
        return;
    }

    window.location.href = resultado.dados.redirect;
});
