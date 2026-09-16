/* Conversão de conta cliente -> técnico (frontend/pages/tornar-tecnico.html).
   Só pede os campos específicos de técnico (nome/email/CPF/endereço já
   existem na conta logada) e envia via fetch multipart pra
   POST /api/conta/tornar-tecnico — que anexa o perfil técnico e troca o
   role da MESMA conta, sem criar uma conta nova. */

const formTornarTecnico = document.getElementById("tornarTecnicoForm");

formTornarTecnico.addEventListener("submit", async (evento) => {
    evento.preventDefault();

    const botao = formTornarTecnico.querySelector("button[type=submit]");
    const textoOriginal = botao.textContent;
    botao.disabled = true;
    botao.textContent = "Enviando...";
    limparMensagem();

    const formData = new FormData(formTornarTecnico);
    // A conta pode já existir de antes desse recurso (sem lat/long
    // capturados no cadastro de cliente) — captura de novo aqui, já que a
    // localização do técnico é o que move o ranking automático.
    anexarCoordenadas(formData, await coordenadasPromise);

    const resultado = await enviarFormulario("/api/conta/tornar-tecnico", formData);

    // Reabilitar SEMPRE: antes, qualquer falha deixava o botão desabilitado
    // para sempre e o usuário sem saber o que tinha acontecido.
    botao.disabled = false;
    botao.textContent = textoOriginal;

    if (!resultado.ok) {
        mostrarErro(resultado.erro);
        return;
    }

    window.location.href = resultado.dados.redirect;
});

avisarSeSemLocalizacao("avisoLocalizacao");
