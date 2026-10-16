/* Perfil público do técnico (funcionalidades 5 e 7), em modal — aberto pelo
   diretório, pelo comparativo de orçamentos e pela tela de perfil do próprio
   técnico ("ver como o cliente vê").

   Mostra só o que GET /api/tecnicos/<id>/perfil-publico devolve: nunca há
   e-mail, telefone ou localização exata. Os certificados são os diplomas que
   o técnico enviou — perfil.html avisa isso a ele.

   Depende de: html-utils.js (escaparHtml), api.js, ui.js (iniciarModal,
   abrirModal, renderizarAvatarHTML, renderizarEstadoErro). */

const PERFIL_PUBLICO_DIAS = [
    "Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira",
    "Sexta-feira", "Sábado", "Domingo",
];

const PERFIL_PUBLICO_MODALIDADES = {
    loja: "Na loja",
    domicilio: "Visita domiciliar",
    remoto: "Suporte remoto",
};

function ppFormatarMoeda(valor) {
    if (valor === null || valor === undefined) return "—";
    return Number(valor).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

/* Horas -> texto curto: "menos de 1 h", "10 h", "2,5 dias". */
function ppFormatarDuracao(horas) {
    if (horas === null || horas === undefined) return "—";
    const valor = Number(horas);
    if (valor < 1) return "menos de 1 h";
    if (valor < 48) return `${valor.toLocaleString("pt-BR", { maximumFractionDigits: 1 })} h`;
    return `${(valor / 24).toLocaleString("pt-BR", { maximumFractionDigits: 1 })} dias`;
}

function ppEstrelas(nota) {
    if (nota === null || nota === undefined) return "Sem avaliações";
    const inteira = Math.round(Number(nota));
    return `${"★".repeat(inteira)}${"☆".repeat(5 - inteira)} ${Number(nota).toLocaleString("pt-BR", { minimumFractionDigits: 1, maximumFractionDigits: 1 })}`;
}

function ppFormatarMes(iso) {
    if (!iso) return "—";
    return new Date(iso).toLocaleDateString("pt-BR", { month: "long", year: "numeric" });
}

function ppRenderizarJanelas(janelas) {
    if (!janelas.length) {
        return `<p class="perfil-publico-vazio">Este técnico ainda não informou horários fixos.</p>`;
    }
    return `<ul class="perfil-publico-janelas">${janelas.map(janela => `
        <li><span>${escaparHtml(PERFIL_PUBLICO_DIAS[janela.dia_semana] || "")}</span>
            <strong>${escaparHtml(janela.inicio)} às ${escaparHtml(janela.fim)}</strong></li>
    `).join("")}</ul>`;
}

function ppRenderizarCriterios(perfil) {
    const criterios = [
        ["Tempo de atendimento", perfil.nota_tempo_media],
        ["Honestidade", perfil.nota_honestidade_media],
        ["Preço justo", perfil.nota_preco_justo_media],
    ].filter(([, nota]) => nota !== null && nota !== undefined);
    if (!criterios.length) return "";
    return `<ul class="perfil-publico-criterios">${criterios.map(([rotulo, nota]) => `
        <li><span>${escaparHtml(rotulo)}</span><strong>${escaparHtml(ppEstrelas(nota))}</strong></li>
    `).join("")}</ul>`;
}

function ppRenderizarCertificados(certificados) {
    if (!certificados.length) {
        return `<p class="perfil-publico-vazio">Nenhum certificado enviado.</p>`;
    }
    return `<ul class="perfil-publico-certificados">${certificados.map((certificado, indice) => `
        <li><a href="${escaparHtml(certificado.url)}" target="_blank" rel="noopener noreferrer">Certificado ${indice + 1}</a></li>
    `).join("")}</ul>`;
}

function ppRenderizarAvaliacoes(avaliacoes) {
    if (!avaliacoes.length) return "";
    return `
        <section class="perfil-publico-secao">
            <h3>O que os clientes dizem</h3>
            <ul class="perfil-publico-avaliacoes">${avaliacoes.map(avaliacao => `
                <li>
                    <div><strong>${escaparHtml(avaliacao.autor)}</strong>
                        <span>${escaparHtml("★".repeat(avaliacao.nota))}</span></div>
                    <p>${escaparHtml(avaliacao.comentario)}</p>
                </li>
            `).join("")}</ul>
        </section>
    `;
}

function renderizarPerfilPublicoHTML(perfil) {
    const selo = perfil.especialista_verificado
        ? `<span class="selo-verificado" title="5 ou mais atendimentos concluídos, nota 4,5 ou mais e certificado enviado">✔ Especialista verificado</span>`
        : "";
    const disponivel = perfil.disponivel_agora
        ? `<span class="badge-disponivel">Disponível agora</span>`
        : "";
    const local = [perfil.cidade, perfil.estado].filter(Boolean).join(" - ");

    const modalidades = (perfil.modalidades || [])
        .map(m => `<span class="chip-modalidade">${escaparHtml(PERFIL_PUBLICO_MODALIDADES[m] || m)}</span>`)
        .join("");

    const sobre = [
        perfil.escolaridade ? `<div><span>Escolaridade</span><p>${escaparHtml(perfil.escolaridade)}</p></div>` : "",
        perfil.curso_superior ? `<div><span>Curso superior</span><p>${escaparHtml(perfil.curso_superior)}</p></div>` : "",
        perfil.regiao_atendimento ? `<div><span>Região de atendimento</span><p>${escaparHtml(perfil.regiao_atendimento)}</p></div>` : "",
        `<div><span>Membro desde</span><p>${escaparHtml(ppFormatarMes(perfil.membro_desde))}</p></div>`,
    ].join("");

    const experiencias = [
        perfil.especializacoes ? `<div><span>Especializações</span><p>${escaparHtml(perfil.especializacoes)}</p></div>` : "",
        perfil.cursos_experiencias ? `<div><span>Cursos e experiências</span><p>${escaparHtml(perfil.cursos_experiencias)}</p></div>` : "",
    ].join("");

    return `
        <header class="perfil-publico-topo">
            ${renderizarAvatarHTML(perfil.nome, perfil.foto_perfil, "avatar-lg")}
            <div>
                <h2>${escaparHtml(perfil.nome)}</h2>
                <p class="perfil-publico-especialidade">${escaparHtml(perfil.especialidade)}${local ? ` · ${escaparHtml(local)}` : ""}</p>
                <p class="perfil-publico-nota">${escaparHtml(ppEstrelas(perfil.nota_media))}
                    <small>(${perfil.total_avaliacoes} avaliaç${perfil.total_avaliacoes === 1 ? "ão" : "ões"})</small></p>
                <div class="perfil-publico-selos">${selo}${disponivel}</div>
            </div>
        </header>

        <div class="perfil-publico-metricas">
            <div><strong>${perfil.atendimentos_concluidos}</strong><span>Atendimentos concluídos</span></div>
            <div><strong>${perfil.taxa_sucesso === null ? "—" : `${perfil.taxa_sucesso}%`}</strong><span>Taxa de sucesso</span></div>
            <div><strong>${escaparHtml(ppFormatarDuracao(perfil.tempo_medio_atendimento_horas))}</strong><span>Tempo médio de atendimento</span></div>
            <div><strong>${escaparHtml(ppFormatarMoeda(perfil.preco_medio))}</strong><span>Preço médio</span></div>
        </div>

        <section class="perfil-publico-secao">
            <h3>Como atende</h3>
            <div class="perfil-publico-chips">${modalidades}</div>
        </section>

        <section class="perfil-publico-secao">
            <h3>Sobre</h3>
            <div class="modal-info-grid">${sobre}</div>
            ${experiencias ? `<div class="modal-info-grid perfil-publico-experiencias">${experiencias}</div>` : ""}
        </section>

        <section class="perfil-publico-secao">
            <h3>Certificados</h3>
            ${ppRenderizarCertificados(perfil.certificados || [])}
        </section>

        <section class="perfil-publico-secao">
            <h3>Disponibilidade semanal</h3>
            ${ppRenderizarJanelas(perfil.janelas || [])}
        </section>

        ${ppRenderizarCriterios(perfil) ? `
        <section class="perfil-publico-secao">
            <h3>Avaliação por critério</h3>
            ${ppRenderizarCriterios(perfil)}
        </section>` : ""}

        ${ppRenderizarAvaliacoes(perfil.ultimas_avaliacoes || [])}
    `;
}

let perfilPublicoOverlay = null;

function garantirModalPerfilPublico() {
    if (perfilPublicoOverlay) return perfilPublicoOverlay;

    const overlay = document.createElement("div");
    overlay.className = "modal-overlay hidden";
    overlay.id = "perfilPublicoOverlay";
    overlay.innerHTML = `
        <div class="modal-card perfil-publico-card">
            <button type="button" class="modal-close" id="perfilPublicoClose" aria-label="Fechar">
                <svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
            </button>
            <div id="perfilPublicoBody"></div>
        </div>
    `;
    document.body.appendChild(overlay);
    iniciarModal(overlay, overlay.querySelector("#perfilPublicoClose"));
    perfilPublicoOverlay = overlay;
    return overlay;
}

async function abrirPerfilPublico(tecnicoId) {
    const overlay = garantirModalPerfilPublico();
    const corpo = overlay.querySelector("#perfilPublicoBody");
    corpo.innerHTML = `<p class="perfil-publico-vazio">Carregando perfil...</p>`;
    abrirModal(overlay);

    const resultado = await obterJson(`/api/tecnicos/${encodeURIComponent(tecnicoId)}/perfil-publico`);
    if (!resultado.ok) {
        renderizarEstadoErro(corpo, resultado.erro, () => abrirPerfilPublico(tecnicoId));
        return;
    }
    corpo.innerHTML = renderizarPerfilPublicoHTML(resultado.dados);
}
