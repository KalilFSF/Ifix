/* "Meus chamados" / Acompanhar chamado (frontend/pages/cliente-chamados.html).
   Lista todos os chamados do cliente logado (GET /api/servicos/meus?como=cliente) e,
   ao clicar em um, mostra o histórico completo de status
   (GET /api/servicos/<id>/historico). Atualiza sozinho via polling. */

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

const HISTORICO_LABELS = {
    aberto: "Chamado aberto",
    aguardando: "Aguardando",
    em_analise: "Em análise",
    em_reparo: "Em reparo",
    finalizado: "Finalizado",
};

const TIPO_LABELS = {
    notebook: "Notebook",
    desktop: "Desktop",
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
            <a href="/cliente/abrir-chamado" class="primary-btn">Abrir primeiro chamado</a>
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
    const tipo = TIPO_LABELS[chamado.tipo_equipamento] || chamado.tipo_equipamento || "—";
    const fotos = chamado.fotos || [];

    elModalBody.innerHTML = `
        <h2>${chamado.titulo}</h2>
        <p class="painel-equipamento">${chamado.codigo} ${chamado.equipamento ? "• " + chamado.equipamento : ""}</p>
        <p class="modal-descricao">${chamado.descricao}</p>

        <div class="modal-info-grid">
            <div><span>Status</span><p><span class="status-badge ${badgeClasse}">${badgeLabel}</span></p></div>
            <div><span>Tipo</span><p>${tipo}</p></div>
            <div><span>Categoria</span><p>${chamado.categoria}</p></div>
            <div><span>Técnico responsável</span><p>${tecnico.nome || "Aguardando definição"}</p></div>
            <div><span>Garantia</span><p>${chamado.garantia ? "Sim (+7% · 10 dias)" : "Não"}</p></div>
        </div>

        ${fotos.length ? `
            <div class="modal-historico">
                <h3>Fotos</h3>
                <div class="fotos-detalhe">
                    ${fotos.map(foto => `<a href="${foto.url}" target="_blank" rel="noopener"><img src="${foto.url}" alt="Foto do chamado"></a>`).join("")}
                </div>
            </div>
        ` : ""}

        <div class="modal-historico">
            <h3>Histórico</h3>
            ${historico.length ? `
                <ul class="historico-list">
                    ${historico.map(item => `
                        <li>
                            <span class="status-badge ${STATUS_BADGE_CLASS[item.status_novo] || ""}">${HISTORICO_LABELS[item.status_novo] || STATUS_LABELS[item.status_novo] || item.status_novo}</span>
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


async function carregarChamados() {
    const resposta = await fetch("/api/servicos/meus?como=cliente");
    if (!resposta.ok) return;
    chamados = await resposta.json();
    renderizarLista();

    if (modalServicoId !== null) {
        await renderizarDetalhe();
    }
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

(async function iniciar() {
    iniciarSidebarMobile();
    const dados = await iniciarRoleChips("cliente");
    if (!dados) return;
    await carregarChamados();

    setInterval(carregarChamados, POLL_INTERVALO_MS);
})();
