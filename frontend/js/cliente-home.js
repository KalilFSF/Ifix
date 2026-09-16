/* Dashboard do cliente (frontend/pages/cliente-home.html).
   O nome do usuário vem de GET /api/me. Os números de resumo e os
   "chamados recentes" vêm de GET /api/servicos/meus?como=cliente. */

const STATUS_ICONES = {
    andamento: '<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"></path>',
    aguardando: '<circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline>',
    concluido: '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline>',
};

const RESUMO_CONFIG = [
    { chave: "andamento", titulo: "Em andamento", variante: "primary" },
    { chave: "aguardando", titulo: "Aguardando", variante: "warning" },
    { chave: "concluido", titulo: "Concluídos", variante: "success" },
];

const MAX_CHAMADOS_RECENTES = 5;

const STATUS_INFO = {
    aberto: { balde: "aguardando", rotulo: "Aguardando técnico", classe: "status-aguardando" },
    aguardando: { balde: "aguardando", rotulo: "Aguardando", classe: "status-aguardando" },
    em_analise: { balde: "andamento", rotulo: "Em análise", classe: "status-analise" },
    em_reparo: { balde: "andamento", rotulo: "Em reparo", classe: "status-reparo" },
    finalizado: { balde: "concluido", rotulo: "Finalizado", classe: "status-concluido" },
};

/* Devolve `ok:false` quando a API falha, em vez do resumo zerado que
   existia antes: um erro de servidor pintava exatamente a mesma tela de
   "Você ainda não possui chamados" que um cliente recém-cadastrado vê. */
async function buscarChamadosDoUsuario() {
    const resultado = await obterLista("/api/servicos/meus?como=cliente");
    if (!resultado.ok) {
        return { ok: false, erro: resultado.erro };
    }

    const chamados = resultado.lista;

    const resumo = { andamento: 0, aguardando: 0, concluido: 0 };
    chamados.forEach(chamado => {
        const info = STATUS_INFO[chamado.status] || STATUS_INFO.aberto;
        resumo[info.balde] += 1;
    });

    const recentes = chamados.slice(0, MAX_CHAMADOS_RECENTES).map(chamado => {
        const info = STATUS_INFO[chamado.status] || STATUS_INFO.aberto;
        return {
            codigo: chamado.codigo,
            equipamento: chamado.equipamento || chamado.categoria,
            titulo: chamado.titulo,
            status: info.rotulo,
            statusClasse: info.classe,
        };
    });

    return { ok: true, resumo, recentes };
}

function iconeSvg(pathInterno) {
    return `<svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${pathInterno}</svg>`;
}

function renderizarResumo(resumo) {
    const container = document.getElementById("statsGrid");
    if (!container) return;

    container.innerHTML = RESUMO_CONFIG.map(item => `
        <div class="stat-card">
            <div>
                <span class="stat-card-title">${item.titulo}</span>
                <span class="stat-card-value">${resumo[item.chave] ?? 0}</span>
            </div>
            <span class="stat-icon stat-icon-${item.variante}">${iconeSvg(STATUS_ICONES[item.chave])}</span>
        </div>
    `).join("");
}

function renderizarEstadoVazio(container) {
    container.innerHTML = `
        <div class="chamados-empty">
            <p class="chamados-empty-titulo">Você ainda não possui chamados.</p>
            <p class="chamados-empty-texto">Quando você abrir um chamado, ele aparecerá aqui.</p>
            <a href="/cliente/abrir-chamado" class="primary-btn">
                ${iconeSvg('<circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="16"></line><line x1="8" y1="12" x2="16" y2="12"></line>')}
                Abrir primeiro chamado
            </a>
        </div>
    `;
}

function renderizarChamadosRecentes(chamados) {
    const container = document.getElementById("chamadosList");
    if (!container) return;

    if (!chamados.length) {
        renderizarEstadoVazio(container);
        return;
    }

    container.innerHTML = chamados.slice(0, MAX_CHAMADOS_RECENTES).map(chamado => `
        <a href="/cliente/chamados" class="chamado-row">
            <div>
                <p class="chamado-meta">${escaparHtml(chamado.codigo)} • ${escaparHtml(chamado.equipamento)}</p>
                <p class="chamado-titulo">${escaparHtml(chamado.titulo)}</p>
            </div>
            <div class="chamado-right">
                <span class="status-badge ${chamado.statusClasse}">${chamado.status}</span>
                ${iconeSvg('<line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline>')}
            </div>
        </a>
    `).join("");
}

async function carregarUsuario(dados) {
    const saudacao = document.getElementById("saudacaoUsuario");
    if (saudacao && dados?.nome) {
        saudacao.textContent = `Olá, ${dados.nome.split(" ")[0]}`;
    }
}

async function carregarDashboard() {
    const resultado = await buscarChamadosDoUsuario();

    if (!resultado.ok) {
        const grid = document.getElementById("statsGrid");
        if (grid) grid.innerHTML = "";
        renderizarEstadoErro(
            document.getElementById("chamadosList"),
            resultado.erro,
            carregarDashboard,
        );
        return;
    }

    renderizarResumo(resultado.resumo);
    renderizarChamadosRecentes(resultado.recentes);
}

(async function () {
    iniciarSidebarMobile();
    const dados = await iniciarRoleChips("cliente");
    if (!dados) return;
    await carregarUsuario(dados);
    await carregarDashboard();
})();
