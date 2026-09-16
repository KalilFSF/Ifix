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

/* Garantia (funcionalidade 2) — espelha GARANTIA_DIAS e os GARANTIA_STATUS_*
   de backend/constants.py. */
const GARANTIA_DIAS = 10;
const GARANTIA_STATUS_LABELS = {
    pendente: "Em análise",
    aprovado: "Aprovado",
    recusado: "Recusado",
    concluido: "Concluído",
};
const MIN_CARACTERES_DESCRICAO_GARANTIA = 15;

const POLL_INTERVALO_MS = 7000;

/* Espelham backend/constants.py: RAIO_SELECAO_TECNICOS_KM e
   MINUTOS_PARA_SUGERIR_AMPLIAR_BUSCA. */
const RAIO_BUSCA_PADRAO_KM = 40;
const MINUTOS_PARA_SUGERIR_AMPLIAR_BUSCA = 15;

const VALORES_GORJETA = [5, 10, 20, 50];

let chamados = [];
let modalServicoId = null;
let meuUsuarioId = null;

/* Assinatura do que o modal mostra agora. O polling de 7s remontava o modal
   inteiro a cada ciclo, o que apagava as notas de avaliação já escolhidas e
   o texto em digitação. Agora a remontagem só acontece quando algo que o
   modal exibe de fato mudou. */
let assinaturaModal = null;
let chatAtual = null;
let gorjetaSelecionada = null;

const elLista = document.getElementById("chamadosList");
const elOverlay = document.getElementById("detalheOverlay");
const elModalBody = document.getElementById("detalheBody");
const elModalClose = document.getElementById("detalheClose");

function formatarData(isoString) {
    if (!isoString) return "";
    return new Date(isoString).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
}

function formatarMoeda(valor) {
    return `R$ ${Number(valor || 0).toFixed(2)}`;
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
                    <p class="chamado-meta">${escaparHtml(chamado.codigo)} • ${escaparHtml(chamado.equipamento || chamado.categoria)}</p>
                    <p class="chamado-titulo">${escaparHtml(chamado.titulo)}</p>
                </div>
                <div class="chamado-right">
                    ${chamado.mensagens_nao_lidas ? `<span class="chat-badge" title="Mensagens não lidas">${chamado.mensagens_nao_lidas}</span>` : ""}
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
    assinaturaModal = null;
    gorjetaSelecionada = null;
    limparRascunhoAvaliacao();
    elOverlay.classList.remove("hidden");
    elModalBody.innerHTML = "<p>Carregando...</p>";
    await renderizarDetalhe();
}

/* Tudo que o modal exibe e que pode mudar sozinho, num só valor comparável.
   As contagens vêm da própria listagem (fn_listar_servicos_participante), o
   que evita refazer as cinco chamadas de detalhe a cada ciclo de polling.
   `mensagens_nao_lidas` fica FORA: o chat se atualiza sozinho, de forma
   incremental, e não deve provocar remontagem — senão a chegada de uma
   mensagem apagaria o que estivesse sendo digitado no resto do modal. */
function calcularAssinatura(chamado) {
    return [
        chamado.id,
        chamado.status,
        chamado.tecnico_id,
        chamado.atualizado_em,
        chamado.aprovacoes_pendentes,
        chamado.solicitacoes_enviadas,
        chamado.orcamentos_recebidos,
        chamado.avaliacoes_total,
        chamado.garantia_dias_restantes,
        chamado.gorjeta,
        chamado.laudo_tecnico ? 1 : 0,
    ].join("|");
}

async function renderizarDetalhe(opcoes = {}) {
    const chamado = chamados.find(item => item.id === modalServicoId);
    if (!chamado) {
        fecharDetalhe();
        return;
    }

    const assinatura = calcularAssinatura(chamado);
    if (!opcoes.forcar && assinatura === assinaturaModal) {
        // Nada mudou: mantém o DOM (e o que a pessoa estiver preenchendo) e
        // só busca as mensagens novas do chat.
        if (chatAtual) await chatAtual.sincronizar();
        return;
    }

    const aguardandoOrcamentos = chamado.status === "aberto";
    const finalizado = chamado.status === "finalizado";

    const [respHistorico, respOrcamentos, respAprovacoes, respGarantia] = await Promise.all([
        obterLista(`/api/servicos/${chamado.id}/historico`),
        aguardandoOrcamentos ? obterLista(`/api/servicos/${chamado.id}/orcamentos`) : Promise.resolve({ ok: true, lista: [] }),
        // Autorizações de custo adicional (funcionalidades 6 e 7): só existem
        // depois que um técnico assumiu o chamado.
        chamado.tecnico_id ? obterLista(`/api/servicos/${chamado.id}/aprovacoes`) : Promise.resolve({ ok: true, lista: [] }),
        // Garantia (funcionalidade 2): só faz sentido buscar se foi contratada
        // e o chamado já foi finalizado — é daí que corre o prazo.
        (chamado.garantia && finalizado) ? obterLista(`/api/servicos/${chamado.id}/garantia`) : Promise.resolve({ ok: true, lista: [] }),
    ]);

    // Antes, qualquer falha aqui virava lista vazia e o modal mostrava
    // "Nenhum orçamento recebido ainda" ou escondia a caixa de autorização
    // pendente — indistinguível de não haver nada mesmo.
    const falha = [respHistorico, respOrcamentos, respAprovacoes, respGarantia].find(item => !item.ok);
    if (falha) {
        assinaturaModal = null;
        renderizarEstadoErro(elModalBody, falha.erro, () => renderizarDetalhe({ forcar: true }));
        return;
    }

    const historico = respHistorico.lista;
    const orcamentos = respOrcamentos.lista;
    const aprovacoes = respAprovacoes.lista;
    const acionamentosGarantia = respGarantia.lista;
    const aprovacoesPendentes = aprovacoes.filter(item => item.status === "pendente");
    const garantiaEmAndamento = acionamentosGarantia.some(
        item => item.status === "pendente" || item.status === "aprovado"
    );

    assinaturaModal = assinatura;

    const tecnico = chamado.tecnico || {};
    const badgeClasse = STATUS_BADGE_CLASS[chamado.status] || "status-aguardando";
    const badgeLabel = STATUS_LABELS[chamado.status] || chamado.status;
    const tipo = TIPO_LABELS[chamado.tipo_equipamento] || chamado.tipo_equipamento || "—";
    const fotos = chamado.fotos || [];
    const podeCancelar = ["aberto", "aguardando"].includes(chamado.status);
    const podeExcluir = chamado.status === "cancelado";

    // Só o cliente encerra o chamado, e só depois que o técnico colocou em
    // reparo e enviou o laudo (ver AtualizarStatusServicoService no backend).
    const podeConcluir = chamado.status === "em_reparo";
    const laudoPronto = Boolean(chamado.laudo_tecnico);

    const chat = criarChat({
        servicoId: chamado.id,
        meuUsuarioId,
        podeConversar: Boolean(chamado.tecnico_id),
    });

    elModalBody.innerHTML = `
        <h2>${escaparHtml(chamado.titulo)}</h2>
        <p class="painel-equipamento">${chamado.codigo} ${chamado.equipamento ? "• " + escaparHtml(chamado.equipamento) : ""}</p>
        <p class="modal-descricao">${escaparHtml(chamado.descricao)}</p>

        ${aprovacoesPendentes.length ? `
            <div class="aprovacao-destaque">
                <h3>Autorização necessária</h3>
                <p class="painel-equipamento">
                    O técnico encontrou um problema adicional. Nada será executado sem a sua autorização.
                </p>
                ${aprovacoesPendentes.map(aprovacao => `
                    <div class="aprovacao-pendente-card">
                        <p class="modal-descricao">${escaparHtml(aprovacao.descricao)}</p>
                        <p class="aprovacao-valor">Custo adicional: <strong>${formatarMoeda(aprovacao.valor_adicional)}</strong></p>
                        <div class="modal-actions">
                            <button type="button" class="primary-btn btn-autorizar" data-id="${aprovacao.id}">Autorizar</button>
                            <button type="button" class="secondary-btn btn-recusar-aprovacao" data-id="${aprovacao.id}">Recusar</button>
                        </div>
                    </div>
                `).join("")}
            </div>
        ` : ""}

        ${aguardandoOrcamentos && !orcamentos.length ? renderizarBuscaVaziaHTML(chamado) : ""}

        <div class="modal-info-grid">
            <div><span>Status</span><p><span class="status-badge ${badgeClasse}">${badgeLabel}</span></p></div>
            <div><span>Tipo</span><p>${tipo}</p></div>
            <div><span>Categoria</span><p>${escaparHtml(chamado.categoria)}</p></div>
            <div><span>Técnico responsável</span><p>${escaparHtml(tecnico.nome || "Aguardando definição")}</p></div>
            <div><span>Garantia</span><p>${chamado.garantia ? `Sim (+7% · ${GARANTIA_DIAS} dias)` : "Não"}</p></div>
            ${chamado.valor_maximo_aprovado !== null && chamado.valor_maximo_aprovado !== undefined ? `
                <div><span>Teto de gasto</span><p>${formatarMoeda(chamado.valor_maximo_aprovado)}</p></div>
            ` : ""}
        </div>

        ${(podeCancelar || podeExcluir || podeConcluir) ? `
            <div class="modal-actions">
                ${podeConcluir ? `
                    <button type="button" class="primary-btn btn-concluir-chamado" data-id="${chamado.id}"
                            ${laudoPronto ? "" : "disabled"}>Confirmar conclusão</button>
                ` : ""}
                ${podeCancelar ? `<button type="button" class="secondary-btn btn-cancelar-chamado" data-id="${chamado.id}">Cancelar chamado</button>` : ""}
                ${podeExcluir ? `<button type="button" class="secondary-btn btn-excluir-chamado" data-id="${chamado.id}">Excluir chamado</button>` : ""}
            </div>
            ${podeConcluir && !laudoPronto ? `
                <p class="painel-equipamento">O técnico ainda não enviou o relatório técnico. Assim que ele enviar, você poderá confirmar a conclusão.</p>
            ` : ""}
        ` : ""}

        ${fotos.length ? `
            <div class="modal-historico">
                <h3>Fotos</h3>
                <div class="fotos-detalhe">
                    ${fotos.map(foto => `<a href="${escaparHtml(foto.url)}" target="_blank" rel="noopener"><img src="${escaparHtml(foto.url)}" alt="Foto do chamado"></a>`).join("")}
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

        ${chamado.garantia && finalizado ? `
            <div class="garantia-bloco">
                <h3>Garantia iFix</h3>
                ${chamado.garantia_ativa ? `
                    <p class="painel-equipamento">
                        ${chamado.garantia_dias_restantes === 0
                            ? "Último dia de cobertura."
                            : `${chamado.garantia_dias_restantes} dia(s) restante(s) de cobertura.`}
                        Se o problema voltou, você pode pedir reembolso ou um novo atendimento gratuito.
                    </p>
                    ${garantiaEmAndamento ? "" : `
                        <button type="button" class="primary-btn" id="btnAbrirGarantia" style="width:auto; margin-top:10px;">
                            Acionar garantia
                        </button>
                        <div class="garantia-form hidden" id="garantiaForm">
                            <div class="input-group">
                                <label for="garantiaDescricao">O que voltou a acontecer?</label>
                                <textarea id="garantiaDescricao" rows="3" placeholder="Descreva o problema que reapareceu."></textarea>
                            </div>
                            <div class="input-group">
                                <label>O que você prefere?</label>
                                <div class="choice-grid" id="garantiaTipos">
                                    <button type="button" class="choice-card is-selected" data-tipo="novo_atendimento">
                                        <strong>Novo atendimento</strong>
                                        <span>Gratuito, com o mesmo técnico</span>
                                    </button>
                                    <button type="button" class="choice-card" data-tipo="reembolso">
                                        <strong>Reembolso</strong>
                                        <span>Devolução do valor pago</span>
                                    </button>
                                </div>
                            </div>
                            <button type="button" class="primary-btn" id="btnConfirmarGarantia" style="width:auto;">
                                Confirmar acionamento
                            </button>
                        </div>
                    `}
                ` : `
                    <p class="painel-equipamento">
                        O prazo de ${GARANTIA_DIAS} dias de cobertura após a finalização já expirou.
                    </p>
                `}
                ${acionamentosGarantia.length ? `
                    <div class="garantia-historico">
                        ${acionamentosGarantia.map(acionamento => `
                            <div class="aprovacao-item is-${acionamento.status}">
                                <div class="aprovacao-item-topo">
                                    <strong>${escaparHtml(acionamento.tipo_solicitado_label || "")}</strong>
                                    <span class="aprovacao-status">${GARANTIA_STATUS_LABELS[acionamento.status] || acionamento.status}</span>
                                </div>
                                <p class="painel-equipamento">${escaparHtml(acionamento.descricao_problema)}</p>
                                ${acionamento.servico_novo_codigo
                                    ? `<p class="painel-equipamento">Chamado gerado: <strong>${escaparHtml(acionamento.servico_novo_codigo)}</strong></p>`
                                    : ""}
                            </div>
                        `).join("")}
                    </div>
                ` : ""}
            </div>
        ` : ""}

        ${aprovacoes.length > aprovacoesPendentes.length ? `
            <div class="modal-historico">
                <h3>Custos adicionais</h3>
                ${aprovacoes.filter(item => item.status !== "pendente").map(aprovacao => `
                    <div class="aprovacao-item is-${aprovacao.status}">
                        <div class="aprovacao-item-topo">
                            <strong>${formatarMoeda(aprovacao.valor_adicional)}</strong>
                            <span class="aprovacao-status">${aprovacao.status === "aprovada" ? "Autorizado" : "Recusado"}</span>
                        </div>
                        <p class="painel-equipamento">${escaparHtml(aprovacao.descricao)}</p>
                    </div>
                `).join("")}
            </div>
        ` : ""}

        ${chamado.laudo_tecnico ? `
            <div class="modal-historico">
                <h3>Relatório técnico</h3>
                <div class="modal-info-grid">
                    <div><span>Causa identificada</span><p>${escaparHtml(chamado.causa_defeito_label || "—")}</p></div>
                </div>
                <p class="modal-descricao">${escaparHtml(chamado.laudo_tecnico)}</p>
                ${chamado.solucao_aplicada ? `
                    <h3 style="margin-top:10px;">O que foi feito</h3>
                    <p class="modal-descricao">${escaparHtml(chamado.solucao_aplicada)}</p>
                ` : ""}
            </div>
        ` : ""}

        ${finalizado ? `
            <div class="modal-historico">
                <h3>Avaliação</h3>
                <div id="avaliacaoContainer"><p class="painel-equipamento">Carregando...</p></div>
            </div>
        ` : ""}

        ${finalizado && chamado.tecnico_id ? renderizarGorjetaHTML(chamado, tecnico) : ""}

        ${chat.montarHTML()}

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
    const btnConcluir = elModalBody.querySelector(".btn-concluir-chamado");
    if (btnCancelar) {
        btnCancelar.addEventListener("click", () => cancelarChamado(Number(btnCancelar.dataset.id)));
    }
    if (btnExcluir) {
        btnExcluir.addEventListener("click", () => excluirChamado(Number(btnExcluir.dataset.id)));
    }
    if (btnConcluir) {
        btnConcluir.addEventListener("click", () => concluirChamado(Number(btnConcluir.dataset.id)));
    }

    ligarBuscaVazia(chamado);
    ligarGorjeta(chamado);

    chatAtual = chat;
    chat.ligar(elModalBody);

    if (aguardandoOrcamentos) {
        elModalBody.querySelectorAll(".btn-escolher-orcamento").forEach(botao => {
            botao.addEventListener("click", () => escolherOrcamento(Number(botao.dataset.id)));
        });
    }

    iniciarFormularioGarantia(chamado.id);

    elModalBody.querySelectorAll(".btn-autorizar").forEach(botao => {
        botao.addEventListener("click", () => responderAprovacao(Number(botao.dataset.id), "aprovada"));
    });
    elModalBody.querySelectorAll(".btn-recusar-aprovacao").forEach(botao => {
        botao.addEventListener("click", () => responderAprovacao(Number(botao.dataset.id), "recusada"));
    });

    if (finalizado) {
        montarBlocoAvaliacao({
            container: document.getElementById("avaliacaoContainer"),
            servicoId: chamado.id,
            meuUsuarioId,
            criteriosQueEnvio: CRITERIOS_AVALIACAO_TECNICO,
            criteriosQueRecebo: CRITERIOS_AVALIACAO_CLIENTE,
            rotuloRecebido: "O técnico avaliou você",
            rotuloEnviado: "Você avaliou o técnico",
            rotuloBotao: "Avaliar técnico",
        });
    }
}


/* ============== Busca sem resposta (ampliar alcance / turbinar valor) ==============

   O chamado podia ficar parado sem nenhum sinal: cliente sem coordenada ou
   base sem técnico geolocalizado produzia zero notificações em silêncio, e
   mesmo com técnicos notificados ninguém é obrigado a orçar. Aqui o cliente
   vê o que aconteceu e tem o que fazer a respeito. */
function renderizarBuscaVaziaHTML(chamado) {
    const semLocalizacao = chamado.latitude === null || chamado.latitude === undefined;
    const ninguemNotificado = !chamado.solicitacoes_enviadas;
    const minutosEsperando = (Date.now() - new Date(chamado.criado_em).getTime()) / 60000;
    const demorando = minutosEsperando >= MINUTOS_PARA_SUGERIR_AMPLIAR_BUSCA;

    if (semLocalizacao) {
        return `
            <div class="busca-vazia">
                <p class="busca-vazia-titulo">Não conseguimos procurar técnicos perto de você</p>
                <p class="busca-vazia-texto">
                    Este chamado foi aberto sem localização, então não dá para medir a distância
                    até os técnicos. Cadastre sua localização no perfil e abra o chamado de novo.
                </p>
                <div class="busca-vazia-acoes">
                    <a href="/perfil" class="primary-btn">Atualizar minha localização</a>
                </div>
            </div>
        `;
    }

    if (!ninguemNotificado && !demorando) return "";

    const raioAtual = chamado.raio_busca_km || RAIO_BUSCA_PADRAO_KM;

    return `
        <div class="busca-vazia">
            <p class="busca-vazia-titulo">
                ${ninguemNotificado
                    ? "Nenhum técnico foi encontrado perto de você"
                    : "Nenhum técnico respondeu ainda"}
            </p>
            <p class="busca-vazia-texto">
                ${ninguemNotificado
                    ? `Não há técnicos cadastrados dentro de ${raioAtual} km. Ampliar a busca procura mais longe.`
                    : `${chamado.solicitacoes_enviadas} técnico(s) foram avisados num raio de ${raioAtual} km, mas ninguém orçou até agora.
                       Você pode procurar mais longe ou aumentar o valor máximo para tornar o chamado mais atraente.`}
            </p>
            <div class="busca-vazia-acoes">
                <button type="button" class="primary-btn" id="btnAmpliarBusca">
                    Ampliar busca para ${raioAtual * 2} km
                </button>
                <div class="busca-vazia-turbinar">
                    <div class="input-group">
                        <label for="novoTeto">Aumentar o valor máximo (R$)</label>
                        <input type="number" id="novoTeto" min="0" step="0.01"
                               placeholder="${chamado.valor_maximo_aprovado || ""}">
                    </div>
                    <button type="button" class="secondary-btn" id="btnAumentarTeto">Atualizar valor</button>
                </div>
            </div>
        </div>
    `;
}

function ligarBuscaVazia(chamado) {
    const btnAmpliar = document.getElementById("btnAmpliarBusca");
    const btnTeto = document.getElementById("btnAumentarTeto");

    if (btnAmpliar) {
        btnAmpliar.addEventListener("click", async () => {
            btnAmpliar.disabled = true;
            btnAmpliar.textContent = "Ampliando...";

            const resultado = await requisitar(`/api/servicos/${chamado.id}/ampliar-busca`, { method: "POST" });

            if (!resultado.ok) {
                btnAmpliar.disabled = false;
                mostrarToast(resultado.erro);
                return;
            }

            const raio = resultado.dados.raio_km;
            const notificados = resultado.dados.tecnicos_notificados;
            mostrarToast(notificados
                ? `Busca ampliada para ${raio} km — ${notificados} técnico(s) avisados.`
                : `Busca ampliada para ${raio} km, mas ainda não encontramos ninguém novo.`);

            await carregarChamados();
            await renderizarDetalhe({ forcar: true });
        });
    }

    if (btnTeto) {
        btnTeto.addEventListener("click", async () => {
            const campo = document.getElementById("novoTeto");
            const valor = campo.value.trim();
            if (!valor) {
                mostrarToast("Informe o novo valor máximo.");
                return;
            }

            btnTeto.disabled = true;
            const resultado = await enviarJson(
                `/api/servicos/${chamado.id}/teto`, { valor_maximo_aprovado: valor }, "PATCH",
            );
            btnTeto.disabled = false;

            if (!resultado.ok) {
                mostrarToast(resultado.erro);
                return;
            }

            mostrarToast("Valor atualizado — os técnicos avisados foram notificados.");
            await carregarChamados();
            await renderizarDetalhe({ forcar: true });
        });
    }
}


/* ============== Gorjeta ==============

   PAGAMENTO: o iFix não processa pagamentos (ver o ponto de extensão em
   backend/constants.py), então aqui a gorjeta é um valor registrado e
   comunicado ao técnico, não uma cobrança. O texto diz isso explicitamente
   pra não prometer o que o sistema ainda não faz. */
function renderizarGorjetaHTML(chamado, tecnico) {
    if (chamado.gorjeta) {
        return `
            <div class="gorjeta-bloco">
                <h3>Gorjeta</h3>
                <p class="gorjeta-registrada">
                    Você registrou ${formatarMoeda(chamado.gorjeta)} de gorjeta para
                    ${escaparHtml(tecnico.nome || "o técnico")}. Combine o repasse diretamente com ele.
                </p>
            </div>
        `;
    }

    return `
        <div class="gorjeta-bloco">
            <h3>Gorjeta (opcional)</h3>
            <p class="painel-equipamento">
                Ficou satisfeito com o atendimento? Registre uma gorjeta para
                ${escaparHtml(tecnico.nome || "o técnico")} — ele é avisado por e-mail e o
                repasse é combinado direto entre vocês.
            </p>
            <div class="gorjeta-sugestoes" id="gorjetaSugestoes">
                ${VALORES_GORJETA.map(valor => `
                    <button type="button" class="gorjeta-opcao" data-valor="${valor}">${formatarMoeda(valor)}</button>
                `).join("")}
            </div>
            <div class="input-group">
                <label for="gorjetaValor">Outro valor (R$)</label>
                <input type="number" id="gorjetaValor" min="0" step="0.01" placeholder="0,00">
            </div>
            <button type="button" class="primary-btn" id="btnGorjeta" style="width:auto;">
                Registrar gorjeta
            </button>
        </div>
    `;
}

function ligarGorjeta(chamado) {
    const sugestoes = document.getElementById("gorjetaSugestoes");
    const campo = document.getElementById("gorjetaValor");
    const botao = document.getElementById("btnGorjeta");
    if (!sugestoes || !campo || !botao) return;

    sugestoes.addEventListener("click", (evento) => {
        const opcao = evento.target.closest(".gorjeta-opcao");
        if (!opcao) return;
        gorjetaSelecionada = Number(opcao.dataset.valor);
        campo.value = "";
        sugestoes.querySelectorAll(".gorjeta-opcao").forEach(item => item.classList.toggle("is-selected", item === opcao));
    });

    // Digitar um valor próprio desmarca a sugestão — senão os dois ficariam
    // aparentemente escolhidos e não daria pra saber qual vale.
    campo.addEventListener("input", () => {
        gorjetaSelecionada = null;
        sugestoes.querySelectorAll(".gorjeta-opcao").forEach(item => item.classList.remove("is-selected"));
    });

    botao.addEventListener("click", async () => {
        const valor = gorjetaSelecionada || Number(campo.value.trim());
        if (!valor || valor <= 0) {
            mostrarToast("Escolha um valor de gorjeta.");
            return;
        }
        if (!confirm(`Registrar ${formatarMoeda(valor)} de gorjeta? O técnico será avisado.`)) return;

        botao.disabled = true;
        const resultado = await enviarJson(`/api/servicos/${chamado.id}/gorjeta`, { valor });
        botao.disabled = false;

        if (!resultado.ok) {
            mostrarToast(resultado.erro);
            return;
        }

        gorjetaSelecionada = null;
        mostrarToast("Gorjeta registrada. O técnico foi avisado.");
        await carregarChamados();
        await renderizarDetalhe({ forcar: true });
    });
}


/* Confirmação de conclusão pelo cliente: o técnico conduz o reparo, mas
   quem recebe o aparelho de volta é o cliente, e só ele sabe se o problema
   foi resolvido. É daqui também que começa a correr o prazo da garantia. */
async function concluirChamado(servicoId) {
    if (!confirm("Confirmar que o serviço foi concluído? O prazo da garantia começa a contar a partir de agora.")) return;

    const resultado = await enviarJson(`/api/servicos/${servicoId}/status`, { status: "finalizado" }, "PATCH");

    if (!resultado.ok) {
        mostrarToast(resultado.erro);
        return;
    }

    mostrarToast("Chamado concluído! Agora você pode avaliar o técnico.");
    await carregarChamados();
    await renderizarDetalhe({ forcar: true });
}

/* Acionamento da garantia (funcionalidade 2): o formulário fica escondido
   atrás do botão pra não poluir o modal de quem só quer ver o chamado. A
   escolha reembolso/novo atendimento usa o mesmo padrão .choice-card da tela
   de abrir chamado. */
function iniciarFormularioGarantia(servicoId) {
    const elAbrir = document.getElementById("btnAbrirGarantia");
    const elForm = document.getElementById("garantiaForm");
    const elTipos = document.getElementById("garantiaTipos");
    const elConfirmar = document.getElementById("btnConfirmarGarantia");
    if (!elAbrir || !elForm || !elTipos || !elConfirmar) return;

    elAbrir.addEventListener("click", () => {
        elForm.classList.remove("hidden");
        elAbrir.classList.add("hidden");
    });

    elTipos.addEventListener("click", (evento) => {
        const botao = evento.target.closest(".choice-card");
        if (!botao) return;
        elTipos.querySelectorAll(".choice-card").forEach(item => item.classList.remove("is-selected"));
        botao.classList.add("is-selected");
    });

    elConfirmar.addEventListener("click", () => acionarGarantia(servicoId));
}

async function acionarGarantia(servicoId) {
    const elDescricao = document.getElementById("garantiaDescricao");
    const elSelecionado = document.querySelector("#garantiaTipos .choice-card.is-selected");
    const elConfirmar = document.getElementById("btnConfirmarGarantia");
    if (!elDescricao || !elSelecionado) return;

    const descricao = elDescricao.value.trim();
    if (descricao.length < MIN_CARACTERES_DESCRICAO_GARANTIA) {
        mostrarToast(`Descreva o problema com pelo menos ${MIN_CARACTERES_DESCRICAO_GARANTIA} caracteres.`);
        return;
    }

    const tipo = elSelecionado.dataset.tipo;
    const confirmacao = tipo === "novo_atendimento"
        ? "Abrir um novo atendimento gratuito com o mesmo técnico?"
        : "Solicitar reembolso do valor pago?";
    if (!confirm(confirmacao)) return;

    elConfirmar.disabled = true;
    const resultado = await enviarJson(`/api/servicos/${servicoId}/garantia`, {
        descricao_problema: descricao,
        tipo_solicitado: tipo,
    });
    elConfirmar.disabled = false;

    if (!resultado.ok) {
        mostrarToast(resultado.erro);
        return;
    }

    const codigoNovo = resultado.dados.acionamento.servico_novo_codigo;
    mostrarToast(codigoNovo
        ? `Garantia acionada. Chamado ${codigoNovo} aberto.`
        : "Garantia acionada. O técnico foi avisado.");
    await carregarChamados();
    await renderizarDetalhe({ forcar: true });
}

/* Autorização remota (funcionalidade 7): o cliente decide de onde estiver se
   o técnico pode ou não executar o serviço adicional. Aprovar eleva o teto
   de gasto do chamado no valor autorizado. */
async function responderAprovacao(aprovacaoId, status) {
    const autorizando = status === "aprovada";
    const pergunta = autorizando
        ? "Autorizar este custo adicional? O valor será somado ao seu teto de gasto."
        : "Recusar este custo adicional? O técnico será orientado a não executar o serviço.";
    if (!confirm(pergunta)) return;

    let justificativa = null;
    if (!autorizando) {
        justificativa = prompt("Quer explicar o motivo da recusa? (opcional)") || null;
    }

    const resultado = await enviarJson(
        `/api/aprovacoes/${aprovacaoId}`, { status, justificativa_recusa: justificativa }, "PATCH",
    );

    if (!resultado.ok) {
        mostrarToast(resultado.erro);
        return;
    }

    mostrarToast(autorizando ? "Custo adicional autorizado." : "Custo adicional recusado.");
    await carregarChamados();
    await renderizarDetalhe({ forcar: true });
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
                <strong>${escaparHtml(tecnico.nome || "Técnico")}</strong>
                <span>${nota}</span>
                ${orcamento.prazo_estimado_dias ? `<span>Prazo estimado: ${orcamento.prazo_estimado_dias} dia(s)</span>` : ""}
                ${orcamento.descricao ? `<span>${escaparHtml(orcamento.descricao)}</span>` : ""}
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

    const resultado = await requisitar(`/api/atendimentos/${atendimentoId}/escolher`, { method: "POST" });

    if (!resultado.ok) {
        mostrarToast(resultado.erro);
        return;
    }

    mostrarToast("Técnico atribuído ao chamado! Agora vocês já podem conversar pelo chat.");
    await carregarChamados();
    await renderizarDetalhe({ forcar: true });
}

function fecharDetalhe() {
    modalServicoId = null;
    assinaturaModal = null;
    chatAtual = null;
    gorjetaSelecionada = null;
    limparRascunhoAvaliacao();
    elOverlay.classList.add("hidden");
    elModalBody.innerHTML = "";
}

async function cancelarChamado(servicoId) {
    if (!confirm("Deseja realmente cancelar este chamado?")) return;

    const resultado = await requisitar(`/api/servicos/${servicoId}/cancelar`, { method: "POST" });

    if (!resultado.ok) {
        mostrarToast(resultado.erro);
        return;
    }

    mostrarToast("Chamado cancelado com sucesso.");
    fecharDetalhe();
    await carregarChamados();
}

async function excluirChamado(servicoId) {
    if (!confirm("Deseja excluir este chamado cancelado? Essa ação não pode ser desfeita.")) return;

    const resultado = await requisitar(`/api/servicos/${servicoId}`, { method: "DELETE" });

    if (!resultado.ok) {
        mostrarToast(resultado.erro);
        return;
    }

    mostrarToast("Chamado excluído com sucesso.");
    fecharDetalhe();
    await carregarChamados();
}

// iniciarModal (js/ui.js) liga o X, o clique fora e o Esc — este último
// nenhum modal do projeto tinha.
iniciarModal(elOverlay, elModalClose, fecharDetalhe);


async function carregarChamados() {
    const resultado = await obterLista("/api/servicos/meus?como=cliente");

    // Antes era `if (!resposta.ok) return;` — a cada 7s a tela congelava nos
    // dados antigos sem nenhum indício de que tinha parado de atualizar.
    if (!resultado.ok) {
        mostrarAvisoConexao(true, resultado.falhaDeRede ? undefined : resultado.erro);
        if (!chamados.length) renderizarEstadoErro(elLista, resultado.erro, carregarChamados);
        return;
    }
    mostrarAvisoConexao(false);
    chamados = resultado.lista;
    renderizarLista();

    if (modalServicoId !== null) {
        await renderizarDetalhe();
    }
}

(async function iniciar() {
    iniciarSidebarMobile();
    const dados = await iniciarRoleChips("cliente");
    if (!dados) return;
    meuUsuarioId = dados.id;
    await carregarChamados();

    setInterval(carregarChamados, POLL_INTERVALO_MS);
})();
