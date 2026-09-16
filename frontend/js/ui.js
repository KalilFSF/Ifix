/* Componentes de interface compartilhados entre as telas.

   Cada um destes estava duplicado em 4 arquivos — e `mostrarToast` em duas
   versões incompatíveis (a de cliente-home.js não usava requestAnimationFrame,
   então a transição CSS nem chegava a disparar). Pior: `mostrarErro`,
   `mostrarToast` e `iniciarSidebarMobile` eram declarados no escopo global de
   cada arquivo, então duas dessas telas na mesma página dariam
   "Identifier has already been declared" e matariam os dois scripts.

   Depende de escaparHtml (html-utils.js) nos estados de erro. */

const TOAST_DURACAO_MS = 2600;
const TOAST_FADE_MS = 250;

function mostrarToast(mensagem) {
    const elToast = document.getElementById("toast");
    if (!elToast) return;

    elToast.textContent = mensagem;
    elToast.classList.remove("hidden");
    // Sem o rAF a classe entra no mesmo frame em que .hidden sai, e o
    // browser não tem estado inicial pra animar a transição a partir dele.
    requestAnimationFrame(() => elToast.classList.add("is-visible"));

    clearTimeout(elToast._timeoutId);
    elToast._timeoutId = setTimeout(() => {
        elToast.classList.remove("is-visible");
        setTimeout(() => elToast.classList.add("hidden"), TOAST_FADE_MS);
    }, TOAST_DURACAO_MS);
}

/* ============== Mensagens inline (login, cadastro, formulários) ============== */

function elementoMensagem(alvo) {
    if (!alvo) return document.getElementById("mensagem");
    return typeof alvo === "string" ? document.getElementById(alvo) : alvo;
}

const VARIANTES_MENSAGEM = ["mensagem-erro", "mensagem-sucesso", "mensagem-aviso"];

/* Alterna classes em vez de sobrescrever className: o elemento pode ser um
   .mensagem (login/cadastro, style.css) ou um .form-erro (abrir chamado,
   dashboard.css), e reescrever a classe inteira apagaria o estilo base. */
function definirMensagem(alvo, texto, variante) {
    const elemento = elementoMensagem(alvo);
    if (!elemento) return;

    elemento.textContent = texto;
    elemento.classList.remove(...VARIANTES_MENSAGEM);
    if (variante && elemento.classList.contains("mensagem")) elemento.classList.add(variante);
    elemento.classList.remove("hidden");
}

function mostrarErro(texto, alvo) {
    definirMensagem(alvo, texto || MENSAGEM_ERRO_GENERICA, "mensagem-erro");
}

function mostrarSucesso(texto, alvo) {
    definirMensagem(alvo, texto, "mensagem-sucesso");
}

function limparMensagem(alvo) {
    const elemento = elementoMensagem(alvo);
    if (!elemento) return;
    elemento.textContent = "";
    elemento.classList.remove(...VARIANTES_MENSAGEM);
    elemento.classList.add("hidden");
}

/* ============== Estado de erro em blocos que carregam dados ==============

   Substitui o padrão `resposta.ok ? json : []`, que mostrava "Nenhum
   orçamento recebido ainda" quando na verdade a chamada falhou. */

function renderizarEstadoErro(container, mensagem, aoTentarNovamente) {
    if (!container) return;
    container.innerHTML = `
        <div class="bloco-erro">
            <p class="bloco-erro-texto">${escaparHtml(mensagem || MENSAGEM_ERRO_GENERICA)}</p>
            <button type="button" class="secondary-btn bloco-erro-btn">Tentar novamente</button>
        </div>
    `;
    const botao = container.querySelector(".bloco-erro-btn");
    if (botao && aoTentarNovamente) botao.addEventListener("click", aoTentarNovamente);
}

/* Faixa discreta pro polling: antes, `if (!resposta.ok) return;` dentro de um
   setInterval de 7s deixava a tela congelada nos dados antigos, sem indício
   nenhum de que ela tinha parado de atualizar. */
function mostrarAvisoConexao(visivel, mensagem) {
    let faixa = document.getElementById("avisoConexao");

    if (!visivel) {
        if (faixa) faixa.remove();
        return;
    }
    if (faixa) return;

    faixa = document.createElement("div");
    faixa.id = "avisoConexao";
    faixa.className = "aviso-conexao";
    faixa.setAttribute("role", "status");
    faixa.textContent = mensagem || "Sem conexão com o servidor — tentando novamente...";
    document.body.appendChild(faixa);
}

/* ============== Modal ============== */

function abrirModal(overlay) {
    if (!overlay) return;
    overlay.classList.remove("hidden");
}

function fecharModal(overlay) {
    if (!overlay) return;
    overlay.classList.add("hidden");
}

/* Liga fechar pelo X, pelo clique fora e pelo Esc (que nenhum modal tinha). */
function iniciarModal(overlay, botaoFechar, aoFechar) {
    if (!overlay) return;

    const fechar = () => {
        fecharModal(overlay);
        if (aoFechar) aoFechar();
    };

    if (botaoFechar) botaoFechar.addEventListener("click", fechar);
    overlay.addEventListener("click", (evento) => {
        if (evento.target === overlay) fechar();
    });
    document.addEventListener("keydown", (evento) => {
        if (evento.key === "Escape" && !overlay.classList.contains("hidden")) fechar();
    });
}

/* ============== Sidebar (drawer no mobile) ============== */

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

/* ============== Avatar ==============

   Usado na sidebar e no card do cliente dentro do modal do técnico. Sem foto,
   cai na inicial do nome — que era o comportamento anterior em todo lugar. */
function renderizarAvatarHTML(nome, fotoUrl, classeExtra = "") {
    const inicial = escaparHtml((nome || "?").charAt(0).toUpperCase());
    if (!fotoUrl) {
        return `<span class="avatar ${classeExtra}">${inicial}</span>`;
    }
    return `<span class="avatar avatar-foto ${classeExtra}"><img src="${escaparHtml(fotoUrl)}" alt="${escaparHtml(nome || "Foto de perfil")}" loading="lazy"></span>`;
}
