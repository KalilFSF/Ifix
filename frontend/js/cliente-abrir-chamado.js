/* Abrir chamado (frontend/pages/cliente-abrir-chamado.html).
   Envia multipart para POST /api/servicos e redireciona para Meus chamados. */

const MAX_FOTOS = 5;
const MAX_BYTES = 2 * 1024 * 1024;
const EXTENSOES = ["png", "jpg", "jpeg", "webp"];

const form = document.getElementById("abrirChamadoForm");
const btnEnviar = document.getElementById("btnEnviar");
const formErro = document.getElementById("formErro");
const inputFotos = document.getElementById("fotos");
const fotosLabel = document.getElementById("fotosLabel");
const fotosPreview = document.getElementById("fotosPreview");
const elToast = document.getElementById("toast");

let arquivosSelecionados = [];

function mostrarToast(mensagem) {
    if (!elToast) return;
    elToast.textContent = mensagem;
    elToast.classList.remove("hidden");
    requestAnimationFrame(() => elToast.classList.add("is-visible"));
    clearTimeout(elToast._timeoutId);
    elToast._timeoutId = setTimeout(() => {
        elToast.classList.remove("is-visible");
        setTimeout(() => elToast.classList.add("hidden"), 250);
    }, 2200);
}

function mostrarErro(texto) {
    formErro.textContent = texto;
    formErro.classList.remove("hidden");
}

function limparErro() {
    formErro.textContent = "";
    formErro.classList.add("hidden");
}

function iniciarChoiceCards() {
    document.querySelectorAll(".choice-card").forEach(card => {
        card.addEventListener("click", () => {
            const grupo = card.dataset.group;
            const valor = card.dataset.value;
            document.querySelectorAll(`.choice-card[data-group="${grupo}"]`).forEach(outro => {
                outro.classList.toggle("is-selected", outro === card);
            });
            const hidden = document.getElementById(grupo);
            if (hidden) hidden.value = valor;
        });
    });
}

function extensaoOk(nome) {
    if (!nome || !nome.includes(".")) return false;
    return EXTENSOES.includes(nome.split(".").pop().toLowerCase());
}

function renderizarFotos() {
    if (!arquivosSelecionados.length) {
        fotosLabel.textContent = "PNG, JPG ou WEBP — até 5 fotos (2 MB cada)";
        fotosPreview.innerHTML = "";
        return;
    }
    fotosLabel.textContent = `${arquivosSelecionados.length} arquivo(s) selecionado(s)`;
    fotosPreview.innerHTML = arquivosSelecionados.map((arquivo, indice) => `
        <li>
            <span>${arquivo.name}</span>
            <button type="button" data-indice="${indice}" aria-label="Remover foto">×</button>
        </li>
    `).join("");
}

function iniciarUpload() {
    inputFotos.addEventListener("change", () => {
        limparErro();
        const novos = Array.from(inputFotos.files || []);
        for (const arquivo of novos) {
            if (!extensaoOk(arquivo.name)) {
                mostrarErro("As fotos devem ser png, jpg, jpeg ou webp.");
                inputFotos.value = "";
                return;
            }
            if (arquivo.size > MAX_BYTES) {
                mostrarErro("Cada foto deve ter no máximo 2 MB.");
                inputFotos.value = "";
                return;
            }
        }
        const juntos = arquivosSelecionados.concat(novos);
        if (juntos.length > MAX_FOTOS) {
            mostrarErro(`Envie no máximo ${MAX_FOTOS} fotos.`);
            inputFotos.value = "";
            return;
        }
        arquivosSelecionados = juntos;
        inputFotos.value = "";
        renderizarFotos();
    });

    fotosPreview.addEventListener("click", (evento) => {
        const botao = evento.target.closest("button[data-indice]");
        if (!botao) return;
        arquivosSelecionados.splice(Number(botao.dataset.indice), 1);
        renderizarFotos();
    });
}

/* O input é type="number" (o próprio navegador já bloqueia letras) — só
   falta validar/normalizar pra 2 casas decimais antes de enviar. */
function parseValorMaximo(valor) {
    const texto = String(valor || "").trim();
    if (!texto) return "";

    const numero = Number(texto);
    if (!Number.isFinite(numero) || numero < 0) return "";

    return numero.toFixed(2);
}

function validarFormulario() {
    const tipo = document.getElementById("tipo_equipamento").value;
    const categoria = document.getElementById("categoria").value;
    const equipamento = document.getElementById("equipamento").value.trim();
    const titulo = document.getElementById("titulo").value.trim();
    const descricao = document.getElementById("descricao").value.trim();
    const valorMaximo = document.getElementById("preco_estimado").value.trim();

    if (!["notebook", "desktop"].includes(tipo)) {
        return "Selecione o tipo de computador.";
    }
    if (!["hardware", "software"].includes(categoria)) {
        return "Selecione a categoria do problema.";
    }
    if (equipamento.length < 2) {
        return "Informe o modelo do equipamento.";
    }
    if (titulo.length < 3) {
        return "Informe um título curto para o problema.";
    }
    if (descricao.length < 10) {
        return "Descreva o problema com mais detalhes.";
    }
    if (valorMaximo) {
        const numero = Number(parseValorMaximo(valorMaximo));
        if (!Number.isFinite(numero) || numero < 0) {
            return "O valor máximo de gasto deve ser um número maior ou igual a zero.";
        }
    }
    return null;
}

function iniciarSidebarMobile() {
    const sidebar = document.getElementById("sidebar");
    const overlay = document.getElementById("sidebarOverlay");
    const btnAbrir = document.getElementById("sidebarOpen");
    const btnFechar = document.getElementById("sidebarClose");
    if (!sidebar || !overlay || !btnAbrir || !btnFechar) return;

    const abrir = () => { sidebar.classList.add("is-open"); overlay.classList.add("is-visible"); };
    const fechar = () => { sidebar.classList.remove("is-open"); overlay.classList.remove("is-visible"); };

    btnAbrir.addEventListener("click", abrir);
    btnFechar.addEventListener("click", fechar);
    overlay.addEventListener("click", fechar);
    document.addEventListener("keydown", (evento) => { if (evento.key === "Escape") fechar(); });
    sidebar.querySelectorAll(".nav-item").forEach(item => item.addEventListener("click", fechar));
}

form.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    limparErro();

    const erro = validarFormulario();
    if (erro) {
        mostrarErro(erro);
        return;
    }

    const body = new FormData();
    const valorMaximoInput = document.getElementById("preco_estimado").value.trim();
    const valorMaximoFormatado = parseValorMaximo(valorMaximoInput);

    body.append("tipo_equipamento", document.getElementById("tipo_equipamento").value);
    body.append("categoria", document.getElementById("categoria").value);
    body.append("equipamento", document.getElementById("equipamento").value.trim());
    body.append("titulo", document.getElementById("titulo").value.trim());
    body.append("descricao", document.getElementById("descricao").value.trim());
    if (valorMaximoFormatado) {
        body.append("preco_estimado", valorMaximoFormatado);
    }
    if (document.getElementById("garantia").checked) {
        body.append("garantia", "1");
    }
    arquivosSelecionados.forEach(arquivo => body.append("fotos", arquivo));

    // Coordenadas do dispositivo no momento do chamado (mais precisas que
    // o endereço cadastrado do cliente, que fica como padrão no backend
    // caso o navegador não consiga geolocalizar agora).
    anexarCoordenadas(body, await coordenadasPromise);

    btnEnviar.disabled = true;
    btnEnviar.textContent = "Enviando...";

    try {
        const resposta = await fetch("/api/servicos", { method: "POST", body });
        const dados = await resposta.json();

        if (!dados.ok) {
            mostrarErro(dados.erro || "Não foi possível abrir o chamado.");
            btnEnviar.disabled = false;
            btnEnviar.textContent = "Enviar chamado";
            return;
        }

        mostrarToast(`Chamado ${dados.servico.codigo} aberto com sucesso.`);
        setTimeout(() => {
            window.location.href = "/cliente/chamados";
        }, 700);
    } catch (_) {
        mostrarErro("Falha de conexão. Tente novamente.");
        btnEnviar.disabled = false;
        btnEnviar.textContent = "Enviar chamado";
    }
});

(async function iniciar() {
    iniciarSidebarMobile();
    iniciarChoiceCards();
    iniciarUpload();
    avisarSeSemLocalizacao("avisoLocalizacao");

    const dados = await iniciarRoleChips("cliente");
    if (!dados) return;

    document.getElementById("nomeUsuario").value = dados.nome || "";
    document.getElementById("telefoneUsuario").value = dados.telefone || "";
})();
