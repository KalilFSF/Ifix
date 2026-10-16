/* Diretório de técnicos (frontend/pages/cliente-tecnicos.html) — funcionalidade 4.

   Lista GET /api/tecnicos/diretorio com os filtros da tela. O diretório mostra
   só dados públicos (sem e-mail, telefone ou localização) e, por decisão do
   grupo, não exibe preço, experiência nem nota de fora do sistema — o preço
   médio aparece só no perfil público, aberto pelo botão "Ver perfil".

   Depende de: html-utils.js, api.js, ui.js, role-chips.js, perfil-publico-ui.js. */

const FILTROS_DEBOUNCE_MS = 350;

const MODALIDADES_CURTAS = {
    loja: "Loja",
    domicilio: "Domicílio",
    remoto: "Remoto",
};

const elForm = document.getElementById("filtrosTecnicos");
const elGrid = document.getElementById("tecnicosGrid");
const elResumo = document.getElementById("tecnicosResumo");

let consultaAtual = 0;
let timerBusca = null;

function lerFiltros() {
    const params = new URLSearchParams();
    const busca = document.getElementById("filtroBusca").value.trim();
    if (busca) params.set("busca", busca);

    [
        ["modalidade", "filtroModalidade"],
        ["categoria", "filtroCategoria"],
        ["nota_minima", "filtroNota"],
        ["ordem", "filtroOrdem"],
    ].forEach(([parametro, id]) => {
        const valor = document.getElementById(id).value;
        if (valor) params.set(parametro, valor);
    });

    if (document.getElementById("filtroDisponivel").checked) params.set("disponivel", "1");
    return params;
}

function notaTexto(tecnico) {
    if (tecnico.nota_media === null || tecnico.nota_media === undefined) return "Sem avaliações";
    const nota = Number(tecnico.nota_media);
    return `${"★".repeat(Math.round(nota))}${"☆".repeat(5 - Math.round(nota))} ${nota.toLocaleString("pt-BR", { minimumFractionDigits: 1, maximumFractionDigits: 1 })} (${tecnico.total_avaliacoes})`;
}

function renderizarCartao(tecnico) {
    const local = [tecnico.cidade, tecnico.estado].filter(Boolean).join(" - ");
    const modalidades = (tecnico.modalidades || [])
        .map(m => `<span class="chip-modalidade">${escaparHtml(MODALIDADES_CURTAS[m] || m)}</span>`)
        .join("");
    const selo = tecnico.especialista_verificado
        ? `<span class="selo-verificado selo-pequeno" title="5 ou mais atendimentos concluídos, nota 4,5 ou mais e certificado enviado">✔ Especialista verificado</span>`
        : "";
    const disponivel = tecnico.disponivel_agora ? `<span class="badge-disponivel">Disponível agora</span>` : "";
    const concluidos = tecnico.atendimentos_concluidos || 0;

    return `
        <article class="tecnico-card">
            <div class="tecnico-card-topo">
                ${renderizarAvatarHTML(tecnico.nome, tecnico.foto_perfil)}
                <div>
                    <h3>${escaparHtml(tecnico.nome)}</h3>
                    <p class="tecnico-card-especialidade">${escaparHtml(tecnico.especialidade)}</p>
                    ${local ? `<p class="tecnico-card-local">${escaparHtml(local)}</p>` : ""}
                </div>
            </div>
            <p class="tecnico-card-nota">${escaparHtml(notaTexto(tecnico))}</p>
            <div class="tecnico-card-selos">${selo}${disponivel}</div>
            <div class="perfil-publico-chips">${modalidades}</div>
            <p class="tecnico-card-metricas">
                ${concluidos} atendimento${concluidos === 1 ? "" : "s"} concluído${concluidos === 1 ? "" : "s"}${tecnico.taxa_sucesso !== null && tecnico.taxa_sucesso !== undefined ? ` · ${tecnico.taxa_sucesso}% de sucesso` : ""}
            </p>
            <button type="button" class="secondary-btn btn-ver-perfil-tecnico" data-id="${tecnico.id}">Ver perfil</button>
        </article>
    `;
}

async function carregarTecnicos() {
    const consulta = ++consultaAtual;
    elResumo.textContent = "Buscando técnicos...";

    const resultado = await obterLista(`/api/tecnicos/diretorio?${lerFiltros()}`);
    // Resposta de uma consulta que já foi substituída por outra mais nova.
    if (consulta !== consultaAtual) return;

    if (!resultado.ok) {
        elResumo.textContent = "";
        renderizarEstadoErro(elGrid, resultado.erro, carregarTecnicos);
        return;
    }

    const lista = resultado.lista;
    elResumo.textContent = lista.length === 1 ? "1 técnico encontrado." : `${lista.length} técnicos encontrados.`;

    if (!lista.length) {
        elGrid.innerHTML = `
            <div class="chamados-empty">
                <p class="chamados-empty-titulo">Nenhum técnico encontrado.</p>
                <p class="chamados-empty-texto">Tente remover algum filtro para ver mais resultados.</p>
            </div>
        `;
        return;
    }
    elGrid.innerHTML = lista.map(renderizarCartao).join("");
}

function iniciarFiltros() {
    // Enter na busca não deve recarregar a página.
    elForm.addEventListener("submit", (evento) => evento.preventDefault());

    document.getElementById("filtroBusca").addEventListener("input", () => {
        clearTimeout(timerBusca);
        timerBusca = setTimeout(carregarTecnicos, FILTROS_DEBOUNCE_MS);
    });
    elForm.querySelectorAll("select, input[type=checkbox]").forEach(campo => {
        campo.addEventListener("change", carregarTecnicos);
    });

    elGrid.addEventListener("click", (evento) => {
        const botao = evento.target.closest(".btn-ver-perfil-tecnico");
        if (botao) abrirPerfilPublico(Number(botao.dataset.id));
    });
}

(async function iniciar() {
    iniciarSidebarMobile();
    const dados = await iniciarRoleChips("cliente");
    if (!dados) return;

    iniciarFiltros();
    carregarTecnicos();
})();
