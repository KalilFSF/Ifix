/* Bloco de avaliação mútua, compartilhado pelos dois painéis.

   Isto estava duplicado byte a byte em cliente-chamados.js e tecnico-home.js,
   inclusive os comentários — o que já tinha custado caro: o mesmo defeito
   (comentário do outro usuário indo cru pro innerHTML) existia nos dois
   lugares e precisava ser corrigido duas vezes.

   A única diferença entre os dois lados é QUAL conjunto de critérios cada um
   preenche e qual recebe, então isso virou parâmetro.

   Depende de: html-utils.js (escaparHtml), api.js, ui.js. */

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
    return criterios
        .map(criterio => `${criterio.rotulo}: ${renderizarEstrelas(avaliacao[`nota_${criterio.chave}`])}`)
        .join(" · ");
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

/* ============== Rascunho ==============

   O modal é remontado sempre que o chamado muda de verdade (e, no painel do
   cliente, o polling podia remontá-lo a cada 7s). Sem guardar as notas fora
   do DOM, o usuário selecionava 1-2-3, o modal se refazia, a seleção sumia
   e o envio ainda acusava "Avalie: Tempo de atendimento, ...". Como o
   rascunho é por chamado, trocar de chamado o descarta sozinho. */
const rascunhoAvaliacao = { servicoId: null, notas: {}, comentario: "" };

function obterRascunhoAvaliacao(servicoId) {
    if (rascunhoAvaliacao.servicoId !== servicoId) {
        rascunhoAvaliacao.servicoId = servicoId;
        rascunhoAvaliacao.notas = {};
        rascunhoAvaliacao.comentario = "";
    }
    return rascunhoAvaliacao;
}

function limparRascunhoAvaliacao() {
    rascunhoAvaliacao.servicoId = null;
    rascunhoAvaliacao.notas = {};
    rascunhoAvaliacao.comentario = "";
}

/* ============== Bloco completo ============== */

async function montarBlocoAvaliacao(opcoes) {
    const {
        container,
        servicoId,
        meuUsuarioId,
        criteriosQueEnvio,
        criteriosQueRecebo,
        rotuloRecebido,
        rotuloEnviado,
        rotuloBotao,
        aoAvaliar,
    } = opcoes;

    if (!container) return;

    const remontar = () => montarBlocoAvaliacao(opcoes);

    const resultado = await obterLista(`/api/servicos/${servicoId}/avaliacoes`);
    // Falha de API não pode virar "ninguém avaliou ainda": antes disso, um
    // erro aqui mostrava o formulário de novo pra quem já tinha avaliado, e
    // o envio batia em "Você já avaliou este chamado."
    if (!resultado.ok) {
        renderizarEstadoErro(container, resultado.erro, remontar);
        return;
    }

    const avaliacoes = resultado.lista;
    const minhaAvaliacao = avaliacoes.find(item => item.autor_id === meuUsuarioId);
    const avaliacaoRecebida = avaliacoes.find(item => item.avaliado_id === meuUsuarioId);

    let html = "";
    if (avaliacaoRecebida) {
        const comentario = avaliacaoRecebida.comentario
            ? ` — "${escaparHtml(avaliacaoRecebida.comentario)}"`
            : "";
        html += `<div class="avaliacao-existente">${rotuloRecebido} — ${renderizarResumoAvaliacaoHTML(avaliacaoRecebida, criteriosQueRecebo)}${comentario}</div>`;
    }

    if (minhaAvaliacao) {
        html += `<div class="avaliacao-existente" style="margin-top:10px;">${rotuloEnviado} — ${renderizarResumoAvaliacaoHTML(minhaAvaliacao, criteriosQueEnvio)}</div>`;
        container.innerHTML = html;
        limparRascunhoAvaliacao();
        return;
    }

    const rascunho = obterRascunhoAvaliacao(servicoId);

    html += `
        <form id="formAvaliacao" style="margin-top:10px;">
            ${renderizarFormAvaliacaoHTML(criteriosQueEnvio)}
            <div class="input-group">
                <label for="avaliacaoComentario">Comentário (opcional)</label>
                <textarea id="avaliacaoComentario" rows="2" placeholder="Como foi o atendimento?"></textarea>
            </div>
            <button type="submit" class="primary-btn" id="btnEnviarAvaliacao">${rotuloBotao}</button>
        </form>
    `;
    container.innerHTML = html;

    const formulario = container.querySelector("#formAvaliacao");
    const campoComentario = container.querySelector("#avaliacaoComentario");

    // Reaplica o que já tinha sido escolhido antes desta remontagem.
    campoComentario.value = rascunho.comentario;
    campoComentario.addEventListener("input", () => { rascunho.comentario = campoComentario.value; });

    formulario.querySelectorAll(".nota-choices").forEach(grupo => {
        const criterio = grupo.dataset.criterio;
        const selecionada = rascunho.notas[criterio];
        if (selecionada) {
            grupo.querySelectorAll(".nota-choice").forEach(item => {
                item.classList.toggle("is-selected", Number(item.dataset.nota) === selecionada);
            });
        }
        grupo.addEventListener("click", (evento) => {
            const botao = evento.target.closest(".nota-choice");
            if (!botao) return;
            rascunho.notas[criterio] = Number(botao.dataset.nota);
            grupo.querySelectorAll(".nota-choice").forEach(item => item.classList.toggle("is-selected", item === botao));
        });
    });

    formulario.addEventListener("submit", async (evento) => {
        evento.preventDefault();

        const faltando = criteriosQueEnvio.filter(criterio => !rascunho.notas[criterio.chave]);
        if (faltando.length) {
            mostrarToast(`Avalie: ${faltando.map(criterio => criterio.rotulo).join(", ")}.`);
            return;
        }

        const botao = container.querySelector("#btnEnviarAvaliacao");
        botao.disabled = true;
        botao.textContent = "Enviando...";

        // As chaves saem dos próprios critérios (nota_tempo, nota_honestidade...)
        // em vez de repetidas à mão — era fácil um lado esquecer uma delas.
        const corpo = { comentario: campoComentario.value.trim() };
        criteriosQueEnvio.forEach(criterio => {
            corpo[`nota_${criterio.chave}`] = rascunho.notas[criterio.chave];
        });

        const envio = await enviarJson(`/api/servicos/${servicoId}/avaliar`, corpo);

        botao.disabled = false;
        botao.textContent = rotuloBotao;

        if (!envio.ok) {
            mostrarToast(envio.erro);
            return;
        }

        mostrarToast("Avaliação enviada!");
        limparRascunhoAvaliacao();
        await remontar();
        if (aoAvaliar) aoAvaliar();
    });
}
