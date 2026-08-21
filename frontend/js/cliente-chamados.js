/* "Meus chamados" / Acompanhar chamado (frontend/pages/cliente-chamados.html).
   Lista todos os chamados do cliente logado (GET /api/servicos/meus) e,
   ao clicar em um, mostra o histórico completo de status
   (GET /api/servicos/<id>/historico). Atualiza sozinho via polling, assim
   as mudanças que o técnico fizer aparecem aqui sem precisar recarregar. */

const STATUS_LABELS = {
    aberto: "Aguardando técnico",
    aguardando: "Aguardando",
    em_analise: "Em análise",
    em_reparo: "Em reparo",
    finalizado: "Finalizado",
};

const STATUS_BADGE_CLASS = {
    aberto: "status-aguardando",
    aguardando: "status-aguardando",
    em_analise: "status-analise",
    em_reparo: "status-reparo",
    finalizado: "status-concluido",
};

const POLL_INTERVALO_MS = 7000;

let chamados = [];
let modalServicoId = null;

const elLista = document.getElementById("chamadosList");
const elOverlay = document.getElementById("detalheOverlay");
const elModalBody = document.getElementById("detalheBody");
const elModalClose = document.getElementById("detalheClose");
const elToast = document.getElementById("toast");


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

function formatarData(isoString) {
    if (!isoString) return "";
    return new Date(isoString).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
}

function iconeSeta() {
    return `<svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline></svg>`;
}

function renderizarVazio() {
    elLista.innerHTML = `
        <div class="chamados-empty">
            <p class="chamados-empty-titulo">Você ainda não possui chamados.</p>
            <p class="chamados-empty-texto">Quando você abrir um chamado, ele aparecerá aqui.</p>
        </div>
    `;
}

function renderizarLista() {
    if (!chamados.length) {
        renderizarVazio();
        return;
    }

    elLista.innerHTML = chamados.map(chamado => {
        const badgeClasse = STATUS_BADGE_CLASS[chamado.status] || "status-aguardando";
        const badgeLabel = STATUS_LABELS[chamado.status] || chamado.status;
        return `
            <button type="button" class="chamado-row" data-id="${chamado.id}">
                <div>
                    <p class="chamado-meta">${chamado.codigo} • ${chamado.equipamento || chamado.categoria}</p>
                    <p class="chamado-titulo">${chamado.titulo}</p>
                </div>
                <div class="chamado-right">
                    <span class="status-badge ${badgeClasse}">${badgeLabel}</span>
                    ${iconeSeta()}
                </div>
            </button>
        `;
    }).join("");
}

elLista.addEventListener("click", (evento) => {
    const linha = evento.target.closest(".chamado-row");
    if (!linha) return;
    abrirDetalhe(Number(linha.getAttribute("data-id")));
});


/* ==================================================
   MODAL DE DETALHE / HISTÓRICO
================================================== */

async function abrirDetalhe(servicoId) {
    modalServicoId = servicoId;
    elOverlay.classList.remove("hidden");
    elModalBody.innerHTML = "<p>Carregando...</p>";
    await renderizarDetalhe();
}

async function renderizarDetalhe() {
    const chamado = chamados.find(item => item.id === modalServicoId);
    if (!chamado) {
        fecharDetalhe();
        return;
    }

    const respostaHistorico = await fetch(`/api/servicos/${chamado.id}/historico`);
    const historico = respostaHistorico.ok ? await respostaHistorico.json() : [];
    const tecnico = chamado.tecnico || {};
    const badgeClasse = STATUS_BADGE_CLASS[chamado.status] || "status-aguardando";
    const badgeLabel = STATUS_LABELS[chamado.status] || chamado.status;

    elModalBody.innerHTML = `
        <h2>${chamado.titulo}</h2>
        <p class="painel-equipamento">${chamado.codigo} ${chamado.equipamento ? "• " + chamado.equipamento : ""}</p>
        <p class="modal-descricao">${chamado.descricao}</p>

        <div class="modal-info-grid">
            <div><span>Status</span><p><span class="status-badge ${badgeClasse}">${badgeLabel}</span></p></div>
            <div><span>Categoria</span><p>${chamado.categoria}</p></div>
            <div><span>Técnico</span><p>${tecnico.nome || "Aguardando um técnico aceitar"}</p></div>
            <div><span>Valor estimado</span><p>R$ ${Number(chamado.preco_estimado || 0).toFixed(2)}</p></div>
        </div>

        <div class="modal-historico">
            <h3>Histórico</h3>
            ${historico.length ? `
                <ul class="historico-list">
                    ${historico.map(item => `
                        <li>
                            <span class="status-badge ${STATUS_BADGE_CLASS[item.status_novo] || ""}">${STATUS_LABELS[item.status_novo] || item.status_novo}</span>
                            <span class="historico-data">${formatarData(item.alterado_em)}</span>
                        </li>
                    `).join("")}
                </ul>
            ` : `<p class="painel-equipamento">Nenhuma atualização registrada ainda.</p>`}
        </div>
    `;
}

function fecharDetalhe() {
    modalServicoId = null;
    elOverlay.classList.add("hidden");
    elModalBody.innerHTML = "";
}

elModalClose.addEventListener("click", fecharDetalhe);
elOverlay.addEventListener("click", (evento) => {
    if (evento.target === elOverlay) fecharDetalhe();
});


/* ==================================================
   CARREGAMENTO / POLLING
================================================== */

async function carregarChamados() {
    const resposta = await fetch("/api/servicos/meus");
    if (!resposta.ok) return;
    chamados = await resposta.json();
    renderizarLista();

    if (modalServicoId !== null) {
        await renderizarDetalhe();
    }
}

async function carregarUsuario() {
    const resposta = await fetch("/api/me");
    if (!resposta.ok) {
        window.location.href = "/";
    }
}

function mostrarToastEmBreve(escopo) {
    (escopo || document).querySelectorAll("[data-em-breve]").forEach(elemento => {
        if (elemento.dataset.stubLigado) return;
        elemento.dataset.stubLigado = "1";
        elemento.addEventListener("click", (evento) => {
            evento.preventDefault();
            mostrarToast("A abertura de chamados chega em breve.");
        });
    });
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

/* Clicar no chip "Técnico" não navega direto pro formulário — primeiro
   mostra este modal de confirmação; só o botão "Quero me tornar técnico"
   dentro dele leva pra /cliente/tornar-tecnico. */
function iniciarModalTornarTecnico() {
    const chip = document.getElementById("chipTornarTecnico");
    const overlay = document.getElementById("tornarTecnicoOverlay");
    const btnFechar = document.getElementById("tornarTecnicoClose");
    if (!chip || !overlay || !btnFechar) return;

    chip.addEventListener("click", () => overlay.classList.remove("hidden"));
    btnFechar.addEventListener("click", () => overlay.classList.add("hidden"));
    overlay.addEventListener("click", (evento) => {
        if (evento.target === overlay) overlay.classList.add("hidden");
    });
}

(async function iniciar() {
    iniciarSidebarMobile();
    iniciarModalTornarTecnico();
    mostrarToastEmBreve();
    await carregarUsuario();
    await carregarChamados();

    setInterval(carregarChamados, POLL_INTERVALO_MS);
})();
