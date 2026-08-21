/* Conversão de conta cliente -> técnico (frontend/pages/tornar-tecnico.html).
   Só pede os campos específicos de técnico (nome/email/CPF/endereço já
   existem na conta logada) e envia via fetch multipart pra
   POST /api/conta/tornar-tecnico — que anexa o perfil técnico e troca o
   role da MESMA conta, sem criar uma conta nova. */

const form = document.getElementById("tornarTecnicoForm");
const mensagem = document.getElementById("mensagem");

function mostrarErro(texto) {
    mensagem.textContent = texto;
    mensagem.className = "mensagem mensagem-erro";
}

form.addEventListener("submit", async (evento) => {
    evento.preventDefault();

    const botao = form.querySelector("button[type=submit]");
    botao.disabled = true;

    const formData = new FormData(form);
    // A conta pode já existir de antes desse recurso (sem lat/long
    // capturados no cadastro de cliente) — captura de novo aqui, já que a
    // localização do técnico é o que move o ranking automático.
    anexarCoordenadas(formData, await coordenadasPromise);

    const resposta = await fetch("/api/conta/tornar-tecnico", {
        method: "POST",
        body: formData,
    });
    const dados = await resposta.json();

    if (!dados.ok) {
        mostrarErro(dados.erro);
        botao.disabled = false;
        return;
    }

    window.location.href = dados.redirect;
});

avisarSeSemLocalizacao("avisoLocalizacao");
