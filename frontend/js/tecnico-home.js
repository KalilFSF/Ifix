/* Painel do técnico (frontend/pages/tecnico-home.html).
   Busca solicitações pendentes (GET /api/tecnico/solicitacoes) e os
   chamados já aceitos pelo técnico logado (GET /api/servicos/meus),
   deixa aceitar/recusar solicitações, filtrar por status/busca, e abrir
   um chamado pra atualizar o status (PATCH /api/servicos/<id>/status) e
   ver o histórico (GET /api/servicos/<id>/historico). Atualiza sozinho a
   cada poucos segundos via polling (não há push/websocket no backend). */

const STATUS_LABELS = {
    aguardando: "Aguardando",
    em_analise: "Em análise",
    em_reparo: "Em reparo",
    finalizado: "Finalizado",
};

const STATUS_BADGE_CLASS = {
    aguardando: "status-aguardando",
    em_analise: "status-analise",
    em_reparo: "status-reparo",
    finalizado: "status-concluido",
};

/* Ordem fixa das etapas do stepper "Progresso do serviço" — o índice de
   cada status nesse array é o que decide quais etapas já foram
   concluídas/qual é a atual/quais ainda são futuras. */
const STATUS_ORDEM = ["aguardando", "em_analise", "em_reparo", "finalizado"];

const STATUS_ICONES = {
    aguardando: '<circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline>',
    em_analise: '<circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line>',
    em_reparo: '<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"></path>',
    finalizado: '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline>',
};

const ICONE_CHECK = '<polyline points="20 6 9 17 4 12"></polyline>';
const ICONE_TELEFONE = '<path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.127.96.362 1.903.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.907.338 1.85.573 2.81.7A2 2 0 0 1 22 16.92z"></path>';
const ICONE_CALENDARIO = '<rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line>';

const TABS = [
    { chave: "todos", titulo: "Todos" },
    { chave: "aguardando", titulo: "Aguardando" },
    { chave: "em_analise", titulo: "Em análise" },
    { chave: "em_reparo", titulo: "Em reparo" },
    { chave: "finalizado", titulo: "Finalizado" },
];

const POLL_INTERVALO_MS = 7000;

let servicos = [];
let solicitacoes = [];
let tabAtiva = "todos";
let termoBusca = "";
let modalServicoId = null;
let modalSolicitacaoId = null;
let meuUsuarioId = null;

const elResumo = document.getElementById("resumoPainel");
const elSolicitacoesSection = document.getElementById("solicitacoesSection");
const elSolicitacoesList = document.getElementById("solicitacoesList");
const elStatusTabs = document.getElementById("statusTabs");
const elBusca = document.getElementById("buscaInput");
const elPainelVazio = document.getElementById("painelVazio");
const elTableWrap = document.getElementById("painelTableWrap");
const elTableBody = document.getElementById("painelTableBody");
const elToast = document.getElementById("toast");

const elOverlay = document.getElementById("detalheOverlay");
const elModalBody = document.getElementById("detalheBody");
const elModalClose = document.getElementById("detalheClose");


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

function formatarMoeda(valor) {
    return `R$ ${Number(valor || 0).toFixed(2)}`;
}

function formatarData(isoString) {
    if (!isoString) return "";
    const data = new Date(isoString);
    return data.toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
}

function formatarDataCurta(isoString) {
    if (!isoString) return "";
    return new Date(isoString).toLocaleDateString("pt-BR");
}

function iconeSvg(pathInterno) {
    return `<svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${pathInterno}</svg>`;
}


/* ==================================================
   SOLICITAÇÕES PENDENTES
================================================== */

async function carregarSolicitacoes() {
    const resposta = await fetch("/api/tecnico/solicitacoes");
    if (!resposta.ok) return;
    solicitacoes = await resposta.json();
    renderizarSolicitacoes();

    // Se a solicitação aberta no modal sumiu da lista (cliente escolheu
    // outro orçamento, por exemplo), fecha o modal em vez de deixar a tela
    // presa numa solicitação que não existe mais.
    if (modalSolicitacaoId !== null && !solicitacoes.some(item => item.id === modalSolicitacaoId)) {
        fecharDetalhe();
    }
}

function renderizarSolicitacoes() {
    if (!solicitacoes.length) {
        elSolicitacoesSection.classList.add("hidden");
        elSolicitacoesList.innerHTML = "";
        return;
    }

    elSolicitacoesSection.classList.remove("hidden");
    elSolicitacoesList.innerHTML = solicitacoes.map(solicitacao => {
        const servico = solicitacao.servico || {};
        const cliente = solicitacao.cliente || {};
        return `
            <article class="solicitacao-card">
                <div>
                    <p class="solicitacao-titulo">${servico.titulo || "Chamado"}</p>
                    <p class="solicitacao-meta">${cliente.nome || "Cliente"} • ${servico.categoria || ""}</p>
                    ${servico.equipamento ? `<p class="solicitacao-meta">${servico.equipamento}</p>` : ""}
                </div>
                <div class="solicitacao-actions">
                    <button type="button" class="primary-btn solicitacao-detalhes" data-id="${solicitacao.id}">Ver detalhes</button>
                </div>
            </article>
        `;
    }).join("");
}

elSolicitacoesList.addEventListener("click", (evento) => {
    const botao = evento.target.closest(".solicitacao-detalhes");
    if (!botao) return;
    abrirDetalheSolicitacao(Number(botao.getAttribute("data-id")));
});


/* ==================================================
   TABS + BUSCA + TABELA
================================================== */

function contarPorStatus() {
    const contagem = { todos: servicos.length };
    TABS.slice(1).forEach(tab => {
        contagem[tab.chave] = servicos.filter(servico => servico.status === tab.chave).length;
    });
    return contagem;
}

function renderizarTabs() {
    const contagem = contarPorStatus();
    elStatusTabs.innerHTML = TABS.map(tab => `
        <button type="button" class="tab-btn ${tab.chave === tabAtiva ? "is-active" : ""}" data-tab="${tab.chave}">
            ${tab.titulo} <span class="tab-count">${contagem[tab.chave] || 0}</span>
        </button>
    `).join("");
}

elStatusTabs.addEventListener("click", (evento) => {
    const botao = evento.target.closest(".tab-btn");
    if (!botao) return;
    tabAtiva = botao.getAttribute("data-tab");
    renderizarTabs();
    renderizarTabela();
});

elBusca.addEventListener("input", () => {
    termoBusca = elBusca.value.trim().toLowerCase();
    renderizarTabela();
});

function servicosFiltrados() {
    let lista = servicos;
    if (tabAtiva !== "todos") {
        lista = lista.filter(servico => servico.status === tabAtiva);
    }
    if (termoBusca) {
        lista = lista.filter(servico => {
            const cliente = servico.cliente || {};
            const alvo = `${servico.codigo} ${cliente.nome || ""} ${servico.titulo}`.toLowerCase();
            return alvo.includes(termoBusca);
        });
    }
    return lista;
}

function renderizarTabela() {
    const lista = servicosFiltrados();

    if (!servicos.length) {
        elPainelVazio.classList.remove("hidden");
        elTableWrap.classList.add("hidden");
        return;
    }

    elPainelVazio.classList.add("hidden");
    elTableWrap.classList.remove("hidden");

    if (!lista.length) {
        elTableBody.innerHTML = `<tr><td colspan="6" class="painel-table-empty">Nenhum chamado encontrado.</td></tr>`;
        return;
    }

    elTableBody.innerHTML = lista.map(servico => {
        const cliente = servico.cliente || {};
        const badgeClasse = STATUS_BADGE_CLASS[servico.status] || "status-aguardando";
        const badgeLabel = STATUS_LABELS[servico.status] || servico.status;
        return `
            <tr class="painel-row" data-id="${servico.id}">
                <td class="painel-codigo">${servico.codigo}</td>
                <td>
                    <p class="painel-problema">${servico.titulo}</p>
                    ${servico.equipamento ? `<p class="painel-equipamento">${servico.equipamento}</p>` : ""}
                </td>
                <td>
                    <p>${cliente.nome || "-"}</p>
                    <p class="painel-equipamento">${cliente.telefone || ""}</p>
                </td>
                <td><span class="status-badge ${badgeClasse}">${badgeLabel}</span></td>
                <td>${formatarMoeda(servico.preco_estimado)}</td>
                <td class="painel-abrir">
                    <svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline></svg>
                </td>
            </tr>
        `;
    }).join("");
}

elTableBody.addEventListener("click", (evento) => {
    const linha = evento.target.closest(".painel-row");
    if (!linha) return;
    abrirDetalhe(Number(linha.getAttribute("data-id")));
});


/* ==================================================
   MODAL DE DETALHE / ATUALIZAÇÃO DE STATUS

   estadoModal guarda o que a TELA está mostrando agora (chamado, status,
   ids de histórico já renderizados) pra que renderizarChamado() só mexa
   no DOM (e só anime) no que realmente mudou em relação ao JSON mais
   recente — nunca substitui o modal inteiro depois da montagem inicial.
================================================== */

let estadoModal = null; // { servicoId, status, historicoIds: Set<number> }

async function abrirDetalhe(servicoId) {
    modalServicoId = servicoId;
    modalSolicitacaoId = null;
    estadoModal = null;
    elOverlay.classList.remove("hidden");
    elModalBody.innerHTML = "<p>Carregando...</p>";

    const servico = servicos.find(item => item.id === servicoId);
    if (!servico) {
        fecharDetalhe();
        return;
    }

    const historico = await buscarHistorico(servicoId);
    await renderizarChamado(servico, historico);
}

async function buscarHistorico(servicoId) {
    const resposta = await fetch(`/api/servicos/${servicoId}/historico`);
    return resposta.ok ? await resposta.json() : [];
}


/* ==================================================
   DETALHE DE UMA SOLICITAÇÃO PENDENTE (ver chamado antes de decidir)
================================================== */

function abrirDetalheSolicitacao(solicitacaoId) {
    const solicitacao = solicitacoes.find(item => item.id === solicitacaoId);
    if (!solicitacao) return;

    modalServicoId = null;
    estadoModal = null;
    modalSolicitacaoId = solicitacaoId;
    elOverlay.classList.remove("hidden");
    montarEstruturaModalSolicitacao(solicitacao);
}

function montarEstruturaModalSolicitacao(solicitacao) {
    const servico = solicitacao.servico || {};
    const cliente = solicitacao.cliente || {};
    const fotos = servico.fotos || [];
    const tipo = servico.tipo_equipamento === "notebook" ? "Notebook"
        : servico.tipo_equipamento === "desktop" ? "Desktop"
        : (servico.tipo_equipamento || "—");

    elModalBody.innerHTML = `
        <h2>${servico.titulo || "Chamado"}</h2>
        <p class="painel-equipamento">${servico.categoria || ""} ${servico.equipamento ? "• " + servico.equipamento : ""}</p>
        <p class="modal-descricao">${servico.descricao || ""}</p>

        <div class="modal-info-grid">
            <div><span>Tipo</span><p>${tipo}</p></div>
            <div><span>Valor de referência do cliente</span><p>${formatarMoeda(servico.preco_estimado)}</p></div>
            <div><span>Cliente</span><p>${cliente.nome || "-"}</p></div>
            <div><span>Telefone</span><p>${cliente.telefone || "-"}</p></div>
        </div>

        ${fotos.length ? `
            <div class="modal-historico">
                <h3>Fotos</h3>
                <div class="fotos-detalhe">
                    ${fotos.map(foto => `<a href="${foto.url}" target="_blank" rel="noopener"><img src="${foto.url}" alt="Foto do chamado"></a>`).join("")}
                </div>
            </div>
        ` : ""}

        <div class="modal-status-control">
            <label>Enviar orçamento</label>
            <p class="historico-item-texto" style="margin-bottom:10px;">Informe o valor e o prazo estimado — o cliente vai comparar com outros orçamentos recebidos antes de escolher.</p>
            <form id="formOrcamento">
                <div class="orcamento-form-grid">
                    <div class="input-group">
                        <label for="orcamentoValor">Valor (R$)</label>
                        <input type="text" id="orcamentoValor" inputmode="decimal" placeholder="R$ 0,00" required>
                    </div>
                    <div class="input-group">
                        <label for="orcamentoPrazo">Prazo estimado (dias)</label>
                        <input type="number" id="orcamentoPrazo" min="1" placeholder="Ex: 3">
                    </div>
                </div>
                <div class="input-group">
                    <label for="orcamentoObservacoes">Observações (opcional)</label>
                    <textarea id="orcamentoObservacoes" rows="3" placeholder="Ex: troca de tela, sujeito a disponibilidade de peça..."></textarea>
                </div>
                <div class="modal-actions">
                    <button type="button" class="secondary-btn" id="btnRecusarSolicitacao">Recusar</button>
                    <button type="submit" class="primary-btn" id="btnEnviarOrcamento">Enviar orçamento</button>
                </div>
            </form>
        </div>
    `;

    document.getElementById("formOrcamento").addEventListener("submit", enviarOrcamento);
    document.getElementById("btnRecusarSolicitacao").addEventListener("click", recusarSolicitacaoModal);
}

function parseMoedaSimples(valor) {
    const texto = String(valor || "").trim().replace(/[R$\s]/gi, "").replace(/\./g, "").replace(",", ".");
    const numero = Number(texto);
    return Number.isFinite(numero) && numero > 0 ? numero : null;
}

async function enviarOrcamento(evento) {
    evento.preventDefault();

    const valor = parseMoedaSimples(document.getElementById("orcamentoValor").value);
    if (valor === null) {
        mostrarToast("Informe um valor de orçamento válido.");
        return;
    }
    const prazo = document.getElementById("orcamentoPrazo").value.trim();
    const observacoes = document.getElementById("orcamentoObservacoes").value.trim();

    const btn = document.getElementById("btnEnviarOrcamento");
    btn.disabled = true;
    btn.textContent = "Enviando...";

    const resposta = await fetch(`/api/tecnico/solicitacoes/${modalSolicitacaoId}/orcamento`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            valor_orcamento: valor,
            prazo_estimado_dias: prazo || null,
            observacoes,
        }),
    });
    const resultado = await resposta.json().catch(() => ({ ok: false }));

    if (!resultado.ok) {
        mostrarToast(resultado.erro || "Não foi possível enviar o orçamento.");
        btn.disabled = false;
        btn.textContent = "Enviar orçamento";
        return;
    }

    mostrarToast("Orçamento enviado! Aguardando o cliente decidir.");
    fecharDetalhe();
    await carregarSolicitacoes();
}

async function recusarSolicitacaoModal() {
    const resposta = await fetch(`/api/tecnico/solicitacoes/${modalSolicitacaoId}/recusar`, { method: "POST" });
    const resultado = await resposta.json().catch(() => ({ ok: false }));

    if (!resultado.ok) {
        mostrarToast(resultado.erro || "Não foi possível recusar.");
        return;
    }

    mostrarToast("Solicitação recusada.");
    fecharDetalhe();
    await carregarSolicitacoes();
}

/* Função central pedida pelo design: recebe o chamado + histórico (JSON
   do backend) e deixa a tela refletindo exatamente esses dados — badge,
   barra de progresso, valor, botões e histórico. É chamada na abertura do
   modal, depois de uma atualização de status (otimista e confirmada) e a
   cada rodada de polling; ela mesma decide se precisa montar a estrutura
   do zero (chamado novo) ou só atualizar o que mudou. */
function renderizarChamado(servico, historico) {
    const precisaMontar = !estadoModal || estadoModal.servicoId !== servico.id;
    const acabouDeFinalizar = !precisaMontar && estadoModal.status !== "finalizado" && servico.status === "finalizado";

    if (precisaMontar || acabouDeFinalizar) {
        montarEstruturaModal(servico);
        estadoModal = { servicoId: servico.id, status: servico.status, historicoIds: new Set() };
        sincronizarHistorico(historico, { animar: false });
        if (servico.status === "finalizado") {
            carregarAvaliacaoTecnico(servico);
        }
        return;
    }

    if (servico.status !== estadoModal.status) {
        estadoModal.status = servico.status;
        aplicarEstadoServico(servico, { animar: true });
    }

    sincronizarHistorico(historico, { animar: true });
}

function montarEstruturaModal(servico) {
    const cliente = servico.cliente || {};
    const badgeClasse = STATUS_BADGE_CLASS[servico.status] || "status-aguardando";
    const badgeLabel = STATUS_LABELS[servico.status] || servico.status;

    elModalBody.innerHTML = `
        <div class="detalhe-topo">
            <div>
                <div class="detalhe-meta-row">
                    <span class="painel-codigo">${servico.codigo}</span>
                    <span class="status-badge ${badgeClasse}" id="detalheBadge">${badgeLabel}</span>
                </div>
                <h2>${servico.titulo}</h2>
                <p class="painel-equipamento">${servico.equipamento || servico.categoria}</p>
            </div>
            <div class="detalhe-valor-card">
                <span>Valor estimado</span>
                <strong id="detalheValor">${formatarMoeda(servico.preco_estimado)}</strong>
                ${servico.garantia ? `<small class="detalhe-garantia">Garantia iFix (+7% · 10 dias)</small>` : ""}
            </div>
        </div>

        <div>
            <h3 style="font-size:14px; margin-bottom:2px;">Progresso do serviço</h3>
            <div class="stepper" id="stepperContainer">${renderizarStepperHTML(servico.status)}</div>
        </div>

        <div class="detalhe-grid">
            <div class="detalhe-col">
                <div class="detalhe-card">
                    <h3>Descrição do problema</h3>
                    <p class="historico-item-texto">${servico.descricao}</p>
                </div>
                <div class="detalhe-card">
                    <h3>Histórico</h3>
                    <ul class="historico-timeline" id="historicoList"></ul>
                </div>
            </div>

            <div class="detalhe-col">
                <div class="detalhe-card">
                    <h3>Cliente</h3>
                    <div class="detalhe-cliente">
                        <span class="detalhe-avatar">${(cliente.nome || "?").charAt(0).toUpperCase()}</span>
                        <p class="detalhe-cliente-nome">${cliente.nome || "-"}</p>
                    </div>
                    <ul class="detalhe-info-list">
                        <li>${iconeSvg(ICONE_TELEFONE)} ${cliente.telefone || "-"}</li>
                        <li>${iconeSvg(ICONE_CALENDARIO)} Aberto em ${formatarDataCurta(servico.criado_em)}</li>
                    </ul>
                </div>

                <div class="detalhe-card">
                    <h3>Atualizar status</h3>
                    <p class="historico-item-texto" style="margin-bottom:6px;">Disponível para o técnico</p>
                    <div class="status-choices" id="statusChoices">
                        ${STATUS_ORDEM.map(status => `
                            <button type="button" class="status-choice ${status === servico.status ? "is-selected" : ""}" data-status="${status}">
                                ${STATUS_LABELS[status]}
                            </button>
                        `).join("")}
                    </div>
                    <button type="button" class="primary-btn" id="statusFinalizarBtn" ${servico.status === "finalizado" ? "disabled" : ""}>
                        Marcar como finalizado
                    </button>
                </div>

                ${servico.status === "finalizado" ? `
                    <div class="detalhe-card" id="avaliacaoCard">
                        <h3>Avaliação</h3>
                        <div id="avaliacaoContainer"><p class="historico-item-texto">Carregando...</p></div>
                    </div>
                ` : ""}
            </div>
        </div>
    `;
}

/* Critérios diferentes por direção — não faz sentido pedir "preço justo"
   do técnico avaliando o cliente. O cliente avalia o SERVIÇO do técnico;
   o técnico avalia o COMPORTAMENTO do cliente (funcionalidade 4). A nota
   geral (média dos critérios de cada conjunto) é calculada no backend. */
const CRITERIOS_AVALIACAO_TECNICO = [
    { chave: "tempo", rotulo: "Tempo de atendimento" },
    { chave: "honestidade", rotulo: "Honestidade" },
    { chave: "preco_justo", rotulo: "Preço justo" },
];
const CRITERIOS_AVALIACAO_CLIENTE = [
    { chave: "comportamento", rotulo: "Comportamento durante o atendimento" },
    { chave: "colaboracao", rotulo: "Colaboração / não interferência no reparo" },
];

function renderizarEstrelas(nota) {
    if (!nota) return "—";
    return "★".repeat(nota) + "☆".repeat(5 - nota);
}

function renderizarResumoAvaliacaoHTML(avaliacao, criterios) {
    return criterios.map(criterio => `${criterio.rotulo}: ${renderizarEstrelas(avaliacao[`nota_${criterio.chave}`])}`).join(" · ");
}

function renderizarFormAvaliacaoHTML(criterios) {
    return criterios.map(criterio => `
        <div class="input-group">
            <label>${criterio.rotulo}</label>
            <div class="nota-choices" data-criterio="${criterio.chave}">
                ${[1, 2, 3, 4, 5].map(nota => `<button type="button" class="nota-choice" data-nota="${nota}">${nota}</button>`).join("")}
            </div>
        </div>
    `).join("");
}

/* Busca as avaliações do chamado e mostra: o que o cliente avaliou sobre o
   técnico (se já avaliou, com os critérios de serviço) e um formulário pra
   o técnico avaliar o COMPORTAMENTO do cliente (se ainda não avaliou) —
   só aparece com o chamado finalizado. */
async function carregarAvaliacaoTecnico(servico) {
    const container = document.getElementById("avaliacaoContainer");
    if (!container) return;

    const resposta = await fetch(`/api/servicos/${servico.id}/avaliacoes`);
    const avaliacoes = resposta.ok ? await resposta.json() : [];
    const minhaAvaliacao = avaliacoes.find(item => item.autor_id === meuUsuarioId);
    const avaliacaoRecebida = avaliacoes.find(item => item.avaliado_id === meuUsuarioId);

    let html = "";
    if (avaliacaoRecebida) {
        html += `<div class="avaliacao-existente">O cliente avaliou você — ${renderizarResumoAvaliacaoHTML(avaliacaoRecebida, CRITERIOS_AVALIACAO_TECNICO)}${avaliacaoRecebida.comentario ? ` — "${avaliacaoRecebida.comentario}"` : ""}</div>`;
    }

    if (minhaAvaliacao) {
        html += `<div class="avaliacao-existente" style="margin-top:10px;">Você avaliou o cliente — ${renderizarResumoAvaliacaoHTML(minhaAvaliacao, CRITERIOS_AVALIACAO_CLIENTE)}</div>`;
        container.innerHTML = html;
        return;
    }

    html += `
        <form id="formAvaliacao" style="margin-top:10px;">
            ${renderizarFormAvaliacaoHTML(CRITERIOS_AVALIACAO_CLIENTE)}
            <div class="input-group">
                <label for="avaliacaoComentario">Comentário (opcional)</label>
                <textarea id="avaliacaoComentario" rows="2" placeholder="Como foi atender esse cliente?"></textarea>
            </div>
            <button type="submit" class="primary-btn" id="btnEnviarAvaliacao">Avaliar cliente</button>
        </form>
    `;
    container.innerHTML = html;

    const notasSelecionadas = {};
    document.querySelectorAll("#formAvaliacao .nota-choices").forEach(grupo => {
        const criterio = grupo.dataset.criterio;
        grupo.addEventListener("click", (evento) => {
            const botao = evento.target.closest(".nota-choice");
            if (!botao) return;
            notasSelecionadas[criterio] = Number(botao.dataset.nota);
            grupo.querySelectorAll(".nota-choice").forEach(item => item.classList.toggle("is-selected", item === botao));
        });
    });

    document.getElementById("formAvaliacao").addEventListener("submit", async (evento) => {
        evento.preventDefault();
        const faltando = CRITERIOS_AVALIACAO_CLIENTE.filter(criterio => !notasSelecionadas[criterio.chave]);
        if (faltando.length) {
            mostrarToast(`Avalie: ${faltando.map(criterio => criterio.rotulo).join(", ")}.`);
            return;
        }
        const comentario = document.getElementById("avaliacaoComentario").value.trim();
        const btn = document.getElementById("btnEnviarAvaliacao");
        btn.disabled = true;

        const resp = await fetch(`/api/servicos/${servico.id}/avaliar`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                nota_comportamento: notasSelecionadas.comportamento,
                nota_colaboracao: notasSelecionadas.colaboracao,
                comentario,
            }),
        });
        const resultado = await resp.json().catch(() => ({ ok: false }));

        if (!resultado.ok) {
            mostrarToast(resultado.erro || "Não foi possível enviar a avaliação.");
            btn.disabled = false;
            return;
        }

        mostrarToast("Avaliação enviada!");
        await carregarAvaliacaoTecnico(servico);
    });
}

/* A última etapa (Finalizado), quando alcançada, conta como "concluída"
   (verde) em vez de "atual" (azul) — não há próxima etapa em andamento,
   então ela deve transmitir conclusão, não "ainda rolando". */
function classificarEtapa(i, indiceAtual) {
    const ultimaEtapaAlcancada = i === indiceAtual && indiceAtual === STATUS_ORDEM.length - 1;
    if (i < indiceAtual || ultimaEtapaAlcancada) return "is-completed";
    if (i === indiceAtual) return "is-current";
    return "is-future";
}

function renderizarStepperHTML(statusAtual) {
    const indiceAtual = STATUS_ORDEM.indexOf(statusAtual);
    return STATUS_ORDEM.map((status, i) => {
        const linhaAntes = i > 0
            ? `<div class="stepper-line ${(i - 1) < indiceAtual ? "is-filled" : ""}"><span class="stepper-line-fill"></span></div>`
            : "";
        const estado = classificarEtapa(i, indiceAtual);
        const icone = estado === "is-completed" ? ICONE_CHECK : STATUS_ICONES[status];

        return `
            ${linhaAntes}
            <div class="stepper-step ${estado}">
                <span class="stepper-icon">${iconeSvg(icone)}</span>
                <span class="stepper-label">${STATUS_LABELS[status]}</span>
            </div>
        `;
    }).join("");
}

/* Atualiza badge + valor + stepper + seleção dos botões de UM chamado já
   montado — sempre via mutação de classes/innerHTML pontual (nunca
   reconstruindo o modal inteiro), pra as transições CSS do stepper
   realmente animarem entre o estado antigo e o novo. */
function aplicarEstadoServico(servico, opcoes = {}) {
    const animar = opcoes.animar !== false;

    const badgeEl = document.getElementById("detalheBadge");
    if (badgeEl) {
        badgeEl.className = `status-badge ${STATUS_BADGE_CLASS[servico.status] || ""}`;
        badgeEl.textContent = STATUS_LABELS[servico.status] || servico.status;
    }

    const valorEl = document.getElementById("detalheValor");
    if (valorEl && servico.preco_estimado !== undefined) {
        valorEl.textContent = formatarMoeda(servico.preco_estimado);
    }

    const indiceAtual = STATUS_ORDEM.indexOf(servico.status);
    const passos = elModalBody.querySelectorAll(".stepper-step");
    const linhas = elModalBody.querySelectorAll(".stepper-line");

    passos.forEach((passo, i) => {
        const jaEstavaNestaEtapa = i === indiceAtual && (passo.classList.contains("is-current") || passo.classList.contains("is-completed"));
        passo.classList.remove("is-completed", "is-current", "is-future");

        const estado = classificarEtapa(i, indiceAtual);
        passo.classList.add(estado);

        const iconeEl = passo.querySelector(".stepper-icon");
        if (iconeEl) iconeEl.innerHTML = iconeSvg(estado === "is-completed" ? ICONE_CHECK : STATUS_ICONES[STATUS_ORDEM[i]]);

        if (animar && i === indiceAtual && !jaEstavaNestaEtapa) {
            const classeAnimacao = servico.status === "finalizado" ? "is-celebrating" : "is-pulsing";
            passo.classList.add(classeAnimacao);
            setTimeout(() => passo.classList.remove(classeAnimacao), 700);
        }
    });

    linhas.forEach((linha, i) => linha.classList.toggle("is-filled", i < indiceAtual));

    elModalBody.querySelectorAll(".status-choice").forEach(botao => {
        botao.classList.toggle("is-selected", botao.dataset.status === servico.status);
    });

    const finalizarBtn = document.getElementById("statusFinalizarBtn");
    if (finalizarBtn && !finalizarBtn.dataset.travado) {
        finalizarBtn.disabled = servico.status === "finalizado";
    }
}

/* Insere só as entradas de histórico que ainda não estavam na tela (com
   animação de entrada); se nada for novo, não toca no DOM — evita
   re-render/animação desnecessária a cada rodada de polling. */
function sincronizarHistorico(historico, opcoes = {}) {
    const animar = opcoes.animar !== false;
    const lista = document.getElementById("historicoList");
    if (!lista || !estadoModal) return;

    if (!historico.length) {
        if (!lista.querySelector(".historico-vazio")) {
            lista.innerHTML = `<li class="historico-vazio">Nenhuma atualização registrada ainda.</li>`;
        }
        estadoModal.historicoIds = new Set();
        return;
    }

    const primeiraRenderizacao = lista.querySelector(".historico-vazio") || estadoModal.historicoIds.size === 0;

    if (primeiraRenderizacao) {
        lista.innerHTML = historico.map(item => renderizarItemHistoricoHTML(item, false)).join("");
    } else {
        const novos = historico.filter(item => !estadoModal.historicoIds.has(item.id));
        novos.forEach(item => {
            lista.insertAdjacentHTML("beforeend", renderizarItemHistoricoHTML(item, animar));
        });
    }

    estadoModal.historicoIds = new Set(historico.map(item => item.id));
}

function renderizarItemHistoricoHTML(item, animar) {
    const badgeClasse = STATUS_BADGE_CLASS[item.status_novo] || "";
    const badgeLabel = STATUS_LABELS[item.status_novo] || item.status_novo;
    return `
        <li class="historico-item ${animar ? "is-entrando" : ""}">
            <div class="historico-item-cabecalho">
                <span class="status-badge ${badgeClasse}">${badgeLabel}</span>
                <span class="historico-data">${formatarData(item.alterado_em)}</span>
            </div>
            ${item.alterado_por_nome ? `<p class="historico-item-texto">Atualizado por ${item.alterado_por_nome}</p>` : ""}
        </li>
    `;
}

function travarBotoesStatus(travado) {
    elModalBody.querySelectorAll(".status-choice").forEach(botao => { botao.disabled = travado; });
    const finalizarBtn = document.getElementById("statusFinalizarBtn");
    if (finalizarBtn) {
        finalizarBtn.dataset.travado = travado ? "1" : "";
        finalizarBtn.disabled = travado || (estadoModal && estadoModal.status === "finalizado");
    }
}

/* Clique num status: feedback visual imediato (otimista) + confirmação
   assíncrona com o backend. Se a API recusar, volta pro status anterior
   e avisa com um toast — nunca deixa a tela "mentindo" sobre o estado real. */
elModalBody.addEventListener("click", async (evento) => {
    const botaoFinalizar = evento.target.closest("#statusFinalizarBtn");
    const botaoEscolha = evento.target.closest(".status-choice");
    if ((!botaoFinalizar && !botaoEscolha) || !estadoModal) return;

    const novoStatus = botaoFinalizar ? "finalizado" : botaoEscolha.dataset.status;
    if (novoStatus === estadoModal.status) return;

    await atualizarStatusDoChamado(novoStatus);
});

async function atualizarStatusDoChamado(novoStatus) {
    const servicoId = estadoModal.servicoId;
    const statusAnterior = estadoModal.status;
    const servicoConhecido = servicos.find(item => item.id === servicoId) || {};

    estadoModal.status = novoStatus;
    aplicarEstadoServico({ status: novoStatus, preco_estimado: servicoConhecido.preco_estimado }, { animar: true });
    travarBotoesStatus(true);

    let resultado;
    try {
        const resposta = await fetch(`/api/servicos/${servicoId}/status`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ status: novoStatus }),
        });
        resultado = await resposta.json();
    } catch {
        resultado = { ok: false };
    }

    if (!resultado.ok) {
        estadoModal.status = statusAnterior;
        aplicarEstadoServico({ status: statusAnterior, preco_estimado: servicoConhecido.preco_estimado }, { animar: false });
        travarBotoesStatus(false);
        mostrarToast(resultado.erro || "Não foi possível atualizar o status. Tente novamente.");
        return;
    }

    travarBotoesStatus(false);
    mostrarToast("Status atualizado.");
    await carregarServicos(); // atualiza tabela/tabs/resumo do painel e reconcilia o modal com os dados oficiais
}

function fecharDetalhe() {
    modalServicoId = null;
    modalSolicitacaoId = null;
    estadoModal = null;
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

async function carregarServicos() {
    const resposta = await fetch("/api/servicos/meus?como=tecnico");
    if (!resposta.ok) return;
    servicos = await resposta.json();

    const ativos = servicos.filter(servico => servico.status !== "finalizado").length;
    elResumo.textContent = ativos
        ? `${ativos} chamado${ativos > 1 ? "s" : ""} ativo${ativos > 1 ? "s" : ""} no momento.`
        : "Nenhum chamado ativo no momento.";

    renderizarTabs();
    renderizarTabela();

    if (modalServicoId !== null) {
        const servicoAberto = servicos.find(item => item.id === modalServicoId);
        if (servicoAberto) {
            const historico = await buscarHistorico(modalServicoId);
            renderizarChamado(servicoAberto, historico);
        } else {
            fecharDetalhe();
        }
    }
}

async function carregarSaudacao() {
    const resposta = await fetch("/api/me");
    if (!resposta.ok) {
        window.location.href = "/";
        return;
    }
    const dados = await resposta.json();
    meuUsuarioId = dados.id;
    elResumo.textContent = `Olá, ${dados.nome.split(" ")[0]}! Carregando seus chamados...`;
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
}

(async function iniciar() {
    iniciarSidebarMobile();
    renderizarTabs();
    await carregarSaudacao();
    await Promise.all([carregarSolicitacoes(), carregarServicos()]);

    setInterval(() => {
        carregarSolicitacoes();
        carregarServicos();
    }, POLL_INTERVALO_MS);
})();
