/* Chat do chamado, compartilhado pelos dois painéis.

   O transporte é polling HTTP, no mesmo tique de 7s que os painéis já usam:
   o deploy é serverless (Vercel), onde uma conexão WebSocket não se sustenta
   entre invocações.

   A renderização é INCREMENTAL — cada mensagem nova é um appendChild, e o
   que já está na tela nunca é reescrito. Reconstruir a lista a cada ciclo
   apagaria o texto sendo digitado no campo e jogaria o scroll pro topo a
   cada 7 segundos, que é o mesmo defeito que o formulário de avaliação
   tinha. Por isso o GET vai com `?desde=<último id>`: o servidor devolve só
   o incremento.

   Depende de: html-utils.js (escaparHtml), api.js, ui.js. */

const CHAT_MAX_CARACTERES = 1000;

function criarChat({ servicoId, meuUsuarioId, podeConversar }) {
    const estado = {
        servicoId,
        meuUsuarioId,
        ultimoId: 0,
        idsExibidos: new Set(),
        elLista: null,
        elCampo: null,
    };

    function montarHTML() {
        if (!podeConversar) {
            return `
                <div class="chat-bloco">
                    <h3 class="detalhe-card-titulo">Conversa</h3>
                    <p class="chat-indisponivel">A conversa com o técnico fica disponível depois que você escolher um orçamento.</p>
                </div>
            `;
        }
        return `
            <div class="chat-bloco">
                <h3 class="detalhe-card-titulo">Conversa</h3>
                <div class="chat-mensagens" id="chatMensagens" aria-live="polite">
                    <p class="chat-vazio" id="chatVazio">Nenhuma mensagem ainda. Diga um oi.</p>
                </div>
                <form class="chat-form" id="chatForm">
                    <textarea id="chatCampo" rows="2" maxlength="${CHAT_MAX_CARACTERES}"
                              placeholder="Escreva sua mensagem..."></textarea>
                    <button type="submit" class="primary-btn" id="chatEnviar">Enviar</button>
                </form>
            </div>
        `;
    }

    function renderizarMensagem(mensagem) {
        const minha = mensagem.autor_id === estado.meuUsuarioId;
        const item = document.createElement("div");
        item.className = `chat-msg ${minha ? "is-minha" : ""}`;
        item.innerHTML = `
            <span class="chat-msg-autor">${escaparHtml(minha ? "Você" : mensagem.autor_nome)}</span>
            <p class="chat-msg-texto">${escaparHtml(mensagem.conteudo)}</p>
            <span class="chat-msg-hora">${formatarHoraChat(mensagem.criado_em)}</span>
        `;
        return item;
    }

    function formatarHoraChat(iso) {
        if (!iso) return "";
        return new Date(iso).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
    }

    async function sincronizar() {
        if (!podeConversar || !estado.elLista) return;

        const url = `/api/servicos/${estado.servicoId}/mensagens${estado.ultimoId ? `?desde=${estado.ultimoId}` : ""}`;
        const resultado = await obterLista(url);
        if (!resultado.ok) {
            // Silencioso de propósito: isto roda em loop de polling, e um
            // toast a cada 7s seria pior que o problema. O aviso geral de
            // conexão do painel já cobre a queda; o erro fica no console.
            return;
        }

        const novas = resultado.lista.filter(mensagem => !estado.idsExibidos.has(mensagem.id));
        if (!novas.length) return;

        const vazio = estado.elLista.querySelector("#chatVazio");
        if (vazio) vazio.remove();

        const coladoNoFim = estado.elLista.scrollHeight - estado.elLista.scrollTop - estado.elLista.clientHeight < 40;

        novas.forEach(mensagem => {
            estado.idsExibidos.add(mensagem.id);
            estado.ultimoId = Math.max(estado.ultimoId, mensagem.id);
            estado.elLista.appendChild(renderizarMensagem(mensagem));
        });

        // Só rola sozinho se a pessoa já estava no fim — senão a chegada de
        // uma mensagem arrancaria ela do trecho que está lendo.
        if (coladoNoFim) estado.elLista.scrollTop = estado.elLista.scrollHeight;

        const recebidas = novas.some(mensagem => mensagem.autor_id !== estado.meuUsuarioId);
        if (recebidas) await requisitar(`/api/servicos/${estado.servicoId}/mensagens/lidas`, { method: "POST" });
    }

    async function enviar(evento) {
        evento.preventDefault();

        const conteudo = estado.elCampo.value.trim();
        if (!conteudo) return;

        const botao = document.getElementById("chatEnviar");
        botao.disabled = true;

        const resultado = await enviarJson(`/api/servicos/${estado.servicoId}/mensagens`, { conteudo });

        botao.disabled = false;

        if (!resultado.ok) {
            mostrarToast(resultado.erro);
            return;
        }

        // Limpa só depois do sucesso: se o envio falhar, o texto continua
        // no campo e a pessoa não perde o que escreveu.
        estado.elCampo.value = "";
        await sincronizar();
    }

    function ligar(container) {
        if (!podeConversar) return;

        estado.elLista = container.querySelector("#chatMensagens");
        estado.elCampo = container.querySelector("#chatCampo");
        estado.idsExibidos = new Set();
        estado.ultimoId = 0;

        container.querySelector("#chatForm").addEventListener("submit", enviar);

        // Enter envia, Shift+Enter quebra linha — o padrão de qualquer chat.
        estado.elCampo.addEventListener("keydown", (evento) => {
            if (evento.key === "Enter" && !evento.shiftKey) {
                evento.preventDefault();
                container.querySelector("#chatForm").requestSubmit();
            }
        });

        sincronizar();
    }

    return { montarHTML, ligar, sincronizar };
}
