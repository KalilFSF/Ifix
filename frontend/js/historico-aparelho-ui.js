/* Histórico do aparelho (funcionalidade 10), compartilhado entre "Abrir
   chamado" (avisa enquanto o cliente digita o modelo) e "Meus chamados"
   (bloco dentro do detalhe do chamado).

   Só mostra chamados do próprio cliente — o backend usa o usuário da sessão.

   Depende de: html-utils.js (escaparHtml), api.js. */

const HISTORICO_APARELHO_DEBOUNCE_MS = 500;
const HISTORICO_APARELHO_MIN_CARACTERES = 2;

const HISTORICO_APARELHO_STATUS = {
    aberto: "Aguardando técnico",
    aguardando: "Aguardando início",
    em_analise: "Em análise",
    em_reparo: "Em reparo",
    finalizado: "Finalizado",
    cancelado: "Cancelado",
};

/* Lista vazia tanto para "sem histórico" quanto para falha de rede: é um
   aviso complementar, e não deve atrapalhar quem só quer abrir o chamado. */
async function carregarHistoricoAparelho(equipamento, excluirServicoId) {
    const modelo = String(equipamento || "").trim();
    if (modelo.length < HISTORICO_APARELHO_MIN_CARACTERES) return [];

    const params = new URLSearchParams({ equipamento: modelo });
    if (excluirServicoId) params.set("excluir", String(excluirServicoId));

    const resultado = await obterLista(`/api/servicos/historico-aparelho?${params}`);
    return resultado.ok ? resultado.lista : [];
}

function formatarDataHistoricoAparelho(iso) {
    if (!iso) return "";
    return new Date(iso).toLocaleDateString("pt-BR");
}

/* Quantas vezes a mesma causa já apareceu neste aparelho — o sinal que o
   cliente quer ver: "isso já aconteceu antes". */
function causaRecorrenteHistoricoAparelho(lista) {
    const contagem = {};
    lista.forEach(item => {
        if (!item.causa_defeito_label) return;
        contagem[item.causa_defeito_label] = (contagem[item.causa_defeito_label] || 0) + 1;
    });
    const recorrentes = Object.entries(contagem).filter(([, total]) => total >= 2);
    if (!recorrentes.length) return null;
    recorrentes.sort((a, b) => b[1] - a[1]);
    return { causa: recorrentes[0][0], total: recorrentes[0][1] };
}

function renderizarHistoricoAparelhoHTML(lista, titulo) {
    if (!lista.length) return "";

    const recorrente = causaRecorrenteHistoricoAparelho(lista);
    const alerta = recorrente
        ? `<p class="historico-aparelho-alerta">Atenção: "${escaparHtml(recorrente.causa)}" já foi a causa ${recorrente.total} vezes neste aparelho.</p>`
        : "";

    const itens = lista.map(item => `
        <li>
            <strong>${escaparHtml(item.codigo)}</strong>
            <span>${escaparHtml(item.titulo)}</span>
            <small>
                ${escaparHtml(HISTORICO_APARELHO_STATUS[item.status] || item.status)}
                · ${escaparHtml(formatarDataHistoricoAparelho(item.criado_em))}
                ${item.causa_defeito_label ? `· Causa: ${escaparHtml(item.causa_defeito_label)}` : ""}
                ${item.tecnico_nome ? `· Técnico: ${escaparHtml(item.tecnico_nome)}` : ""}
            </small>
        </li>
    `).join("");

    return `
        <p class="historico-aparelho-titulo">${escaparHtml(titulo)}</p>
        ${alerta}
        <ul class="historico-aparelho-lista">${itens}</ul>
    `;
}

/* Liga o campo de modelo ao aviso: consulta depois de uma pausa na digitação
   e descarta respostas que chegam fora de ordem. */
function iniciarHistoricoAparelho(inputId, containerId) {
    const input = document.getElementById(inputId);
    const container = document.getElementById(containerId);
    if (!input || !container) return;

    let timer = null;
    let ultimaConsulta = 0;

    async function atualizar() {
        const consulta = ++ultimaConsulta;
        const lista = await carregarHistoricoAparelho(input.value);
        if (consulta !== ultimaConsulta) return;

        const total = lista.length;
        const titulo = total === 1
            ? "Você já abriu 1 chamado para este aparelho:"
            : `Você já abriu ${total} chamados para este aparelho:`;
        container.innerHTML = renderizarHistoricoAparelhoHTML(lista, titulo);
        container.classList.toggle("hidden", total === 0);
    }

    input.addEventListener("input", () => {
        clearTimeout(timer);
        timer = setTimeout(atualizar, HISTORICO_APARELHO_DEBOUNCE_MS);
    });
    input.addEventListener("blur", () => {
        clearTimeout(timer);
        atualizar();
    });
}
