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
    cancelado: "Cancelado",
};

const STATUS_BADGE_CLASS = {
    aberto: "status-aguardando",
    aguardando: "status-aguardando",
    em_analise: "status-analise",
    em_reparo: "status-reparo",
    finalizado: "status-concluido",
    cancelado: "status-cancelado",
};

const HISTORICO_LABELS = {
    aberto: "Chamado aberto",
    aguardando: "Aguardando",
    em_analise: "Em análise",
    em_reparo: "Em reparo",
    finalizado: "Finalizado",
    cancelado: "Cancelado",
};

const TIPO_LABELS = {
    notebook: "Notebook",
    desktop: "Desktop",
};

const POLL_INTERVALO_MS = 7000;

let chamados = [];
let modalServicoId = null;
let meuUsuarioId = null;

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

function formatarMoeda(valor) {
    return `R$ ${Number(valor || 0).toFixed(2)}`;
}

function renderizarEstrelas(nota) {
    return "★".repeat(nota) + "☆".repeat(5 - nota);
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

    const aguardandoOrcamentos = chamado.status === "aberto";
    let orcamentos = [];
    if (aguardandoOrcamentos) {
        const respostaOrcamentos = await fetch(`/api/servicos/${chamado.id}/orcamentos`);
        orcamentos = respostaOrcamentos.ok ? await respostaOrcamentos.json() : [];
    }

    const finalizado = chamado.status === "finalizado";
    let avaliacoes = [];
    if (finalizado) {
        const respostaAvaliacoes = await fetch(`/api/servicos/${chamado.id}/avaliacoes`);
        avaliacoes = respostaAvaliacoes.ok ? await respostaAvaliacoes.json() : [];
    }

    const tecnico = chamado.tecnico || {};
    const badgeClasse = STATUS_BADGE_CLASS[chamado.status] || "status-aguardando";
    const badgeLabel = STATUS_LABELS[chamado.status] || chamado.status;
    const tipo = TIPO_LABELS[chamado.tipo_equipamento] || chamado.tipo_equipamento || "—";
    const fotos = chamado.fotos || [];
    const podeCancelar = ["aberto", "aguardando"].includes(chamado.status);
    const podeExcluir = chamado.status === "cancelado";

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

        ${(podeCancelar || podeExcluir) ? `
            <div class="modal-actions">
                ${podeCancelar ? `<button type="button" class="secondary-btn btn-cancelar-chamado" data-id="${chamado.id}">Cancelar chamado</button>` : ""}
                ${podeExcluir ? `<button type="button" class="secondary-btn btn-excluir-chamado" data-id="${chamado.id}">Excluir chamado</button>` : ""}
            </div>
        ` : ""}

        ${fotos.length ? `
            <div class="modal-historico">
                <h3>Fotos</h3>
                <div class="fotos-detalhe">
                    ${fotos.map(foto => `<a href="${foto.url}" target="_blank" rel="noopener"><img src="${foto.url}" alt="Foto do chamado"></a>`).join("")}
                </div>
            </div>
        ` : ""}

        ${aguardandoOrcamentos ? `
            <div class="modal-historico">
                <h3>Orçamentos recebidos</h3>
                ${orcamentos.length ? `
                    <div class="orcamentos-list">
                        ${orcamentos.map(orcamento => renderizarOrcamentoHTML(orcamento)).join("")}
                    </div>
                ` : `<p class="painel-equipamento">Nenhum orçamento recebido ainda — os técnicos selecionados foram notificados.</p>`}
            </div>
        ` : ""}

        ${finalizado ? `
            <div class="modal-historico">
                <h3>Avaliação</h3>
                <div id="avaliacaoContainer"><p class="painel-equipamento">Carregando...</p></div>
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

    const btnCancelar = elModalBody.querySelector(".btn-cancelar-chamado");
    const btnExcluir = elModalBody.querySelector(".btn-excluir-chamado");
    if (btnCancelar) {
        btnCancelar.addEventListener("click", () => cancelarChamado(Number(btnCancelar.dataset.id)));
    }
    if (btnExcluir) {
        btnExcluir.addEventListener("click", () => excluirChamado(Number(btnExcluir.dataset.id)));
    }

    if (aguardandoOrcamentos) {
        elModalBody.querySelectorAll(".btn-escolher-orcamento").forEach(botao => {
            botao.addEventListener("click", () => escolherOrcamento(Number(botao.dataset.id)));
        });
    }

    if (finalizado) {
        carregarAvaliacaoCliente(chamado);
    }
}

function renderizarOrcamentoHTML(orcamento) {
    const tecnico = orcamento.tecnico || {};
    const nota = tecnico.nota_media !== null && tecnico.nota_media !== undefined
        ? `${renderizarEstrelas(Math.round(tecnico.nota_media))} (${tecnico.nota_media.toFixed(1)})`
        : "Sem avaliações ainda";
    const statusClasse = orcamento.status === "aceito" ? "is-aceito" : orcamento.status === "recusado" ? "is-recusado" : "";

    return `
        <article class="orcamento-card ${statusClasse}">
            <div class="orcamento-info">
                <strong>${tecnico.nome || "Técnico"}</strong>
                <span>${nota}</span>
                ${orcamento.prazo_estimado_dias ? `<span>Prazo estimado: ${orcamento.prazo_estimado_dias} dia(s)</span>` : ""}
                ${orcamento.descricao ? `<span>${orcamento.descricao}</span>` : ""}
            </div>
            <div style="display:flex; align-items:center; gap:12px;">
                <span class="orcamento-valor">${formatarMoeda(orcamento.valor_orcamento)}</span>
                ${orcamento.status === "pendente" ? `<button type="button" class="primary-btn btn-escolher-orcamento" data-id="${orcamento.id}" style="width:auto; margin:0;">Escolher</button>` : `<span class="status-badge">${orcamento.status === "aceito" ? "Escolhido" : "Não escolhido"}</span>`}
            </div>
        </article>
    `;
}

async function escolherOrcamento(atendimentoId) {
    if (!confirm("Confirmar este orçamento? Os demais técnicos serão avisados que o chamado foi atribuído a outro profissional.")) return;

    const resposta = await fetch(`/api/atendimentos/${atendimentoId}/escolher`, { method: "POST" });
    const resultado = await resposta.json().catch(() => ({ ok: false }));

    if (!resultado.ok) {
        mostrarToast(resultado.erro || "Não foi possível escolher este orçamento.");
        return;
    }

    mostrarToast("Técnico atribuído ao chamado!");
    await carregarChamados();
}

/* Busca as avaliações do chamado finalizado: mostra o que o técnico
   avaliou sobre o cliente (se já avaliou) e um formulário pra o cliente
   avaliar o técnico (se ainda não avaliou). */
async function carregarAvaliacaoCliente(chamado) {
    const container = document.getElementById("avaliacaoContainer");
    if (!container) return;

    const resposta = await fetch(`/api/servicos/${chamado.id}/avaliacoes`);
    const avaliacoes = resposta.ok ? await resposta.json() : [];
    const minhaAvaliacao = avaliacoes.find(item => item.autor_id === meuUsuarioId);
    const avaliacaoRecebida = avaliacoes.find(item => item.avaliado_id === meuUsuarioId);

    let html = "";
    if (avaliacaoRecebida) {
        html += `<div class="avaliacao-existente">O técnico avaliou você: ${renderizarEstrelas(avaliacaoRecebida.nota)}${avaliacaoRecebida.comentario ? ` — "${avaliacaoRecebida.comentario}"` : ""}</div>`;
    }

    if (minhaAvaliacao) {
        html += `<div class="avaliacao-existente" style="margin-top:10px;">Você avaliou o técnico: ${renderizarEstrelas(minhaAvaliacao.nota)}</div>`;
        container.innerHTML = html;
        return;
    }

    html += `
        <form id="formAvaliacao" style="margin-top:10px;">
            <div class="nota-choices" id="notaChoices">
                ${[1, 2, 3, 4, 5].map(nota => `<button type="button" class="nota-choice" data-nota="${nota}">${nota}</button>`).join("")}
            </div>
            <div class="input-group">
                <label for="avaliacaoComentario">Comentário (opcional)</label>
                <textarea id="avaliacaoComentario" rows="2" placeholder="Como foi o atendimento?"></textarea>
            </div>
            <button type="submit" class="primary-btn" id="btnEnviarAvaliacao">Avaliar técnico</button>
        </form>
    `;
    container.innerHTML = html;

    let notaSelecionada = null;
    document.getElementById("notaChoices").addEventListener("click", (evento) => {
        const botao = evento.target.closest(".nota-choice");
        if (!botao) return;
        notaSelecionada = Number(botao.dataset.nota);
        document.querySelectorAll("#notaChoices .nota-choice").forEach(item => item.classList.toggle("is-selected", item === botao));
    });

    document.getElementById("formAvaliacao").addEventListener("submit", async (evento) => {
        evento.preventDefault();
        if (!notaSelecionada) {
            mostrarToast("Selecione uma nota de 1 a 5.");
            return;
        }
        const comentario = document.getElementById("avaliacaoComentario").value.trim();
        const btn = document.getElementById("btnEnviarAvaliacao");
        btn.disabled = true;

        const resp = await fetch(`/api/servicos/${chamado.id}/avaliar`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ nota: notaSelecionada, comentario }),
        });
        const resultado = await resp.json().catch(() => ({ ok: false }));

        if (!resultado.ok) {
            mostrarToast(resultado.erro || "Não foi possível enviar a avaliação.");
            btn.disabled = false;
            return;
        }

        mostrarToast("Avaliação enviada!");
        await carregarAvaliacaoCliente(chamado);
    });
}

function fecharDetalhe() {
    modalServicoId = null;
    elOverlay.classList.add("hidden");
    elModalBody.innerHTML = "";
}

async function cancelarChamado(servicoId) {
    if (!confirm("Deseja realmente cancelar este chamado?")) return;

    const resposta = await fetch(`/api/servicos/${servicoId}/cancelar`, { method: "POST" });
    const dados = await resposta.json();

    if (!resposta.ok || !dados.ok) {
        mostrarToast(dados.erro || "Não foi possível cancelar este chamado.");
        return;
    }

    mostrarToast("Chamado cancelado com sucesso.");
    fecharDetalhe();
    await carregarChamados();
}

async function excluirChamado(servicoId) {
    if (!confirm("Deseja excluir este chamado cancelado? Essa ação não pode ser desfeita.")) return;

    const resposta = await fetch(`/api/servicos/${servicoId}`, { method: "DELETE" });
    const dados = await resposta.json();

    if (!resposta.ok || !dados.ok) {
        mostrarToast(dados.erro || "Não foi possível excluir este chamado.");
        return;
    }

    mostrarToast("Chamado excluído com sucesso.");
    fecharDetalhe();
    await carregarChamados();
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
    meuUsuarioId = dados.id;
    await carregarChamados();

    setInterval(carregarChamados, POLL_INTERVALO_MS);
})();
