/* Sino de notificações (funcionalidade 9), compartilhado pelos painéis.

   Substitui o aviso por WhatsApp/SMS por algo que não depende de plataforma
   externa: o sino aparece em qualquer tela autenticada que carregue este
   script, e atualiza no mesmo ritmo de polling dos painéis (7 s).

   O botão é injetado aqui, e não repetido no HTML de cada página, pra o
   sino não divergir entre as telas.

   Depende de: html-utils.js (escaparHtml), api.js, ui.js (mostrarToast). */

const NOTIFICACOES_POLLING_MS = 7000;

const NOTIFICACOES_ICONE_SINO = `
    <svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
        <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
    </svg>`;

(function iniciarNotificacoes() {
    let botao = null;
    let painel = null;
    let contador = null;
    let lista = [];
    let naoLidas = 0;
    let primeiraCarga = true;
    let timer = null;

    function formatarQuando(iso) {
        if (!iso) return "";
        const diferencaMin = Math.max(0, Math.round((Date.now() - new Date(iso).getTime()) / 60000));
        if (diferencaMin < 1) return "agora";
        if (diferencaMin < 60) return `há ${diferencaMin} min`;
        if (diferencaMin < 1440) return `há ${Math.floor(diferencaMin / 60)} h`;
        return new Date(iso).toLocaleDateString("pt-BR");
    }

    function renderizarContador() {
        contador.textContent = naoLidas > 99 ? "99+" : String(naoLidas);
        contador.classList.toggle("hidden", naoLidas === 0);
        botao.setAttribute(
            "aria-label",
            naoLidas ? `Notificações: ${naoLidas} não lida${naoLidas === 1 ? "" : "s"}` : "Notificações",
        );
    }

    function renderizarLista() {
        if (!lista.length) {
            painel.querySelector(".notif-lista").innerHTML =
                `<li class="notif-vazio">Nenhuma notificação por enquanto.</li>`;
            return;
        }
        painel.querySelector(".notif-lista").innerHTML = lista.map(item => `
            <li>
                <a class="notif-item ${item.lida ? "" : "is-nova"}" href="${escaparHtml(item.link || "#")}">
                    <strong>${escaparHtml(item.titulo)}</strong>
                    <span>${escaparHtml(item.mensagem)}</span>
                    <small>${escaparHtml(formatarQuando(item.criado_em))}</small>
                </a>
            </li>
        `).join("");
    }

    async function carregar() {
        if (document.hidden) return;
        const resultado = await obterJson("/api/notificacoes");
        // Falha de rede/servidor não vira toast a cada 7 s: o sino só fica como está.
        if (!resultado.ok) return;

        const anterior = naoLidas;
        lista = resultado.dados.notificacoes || [];
        naoLidas = resultado.dados.nao_lidas || 0;
        renderizarContador();
        if (!painel.classList.contains("hidden")) renderizarLista();

        if (!primeiraCarga && naoLidas > anterior && lista.length && typeof mostrarToast === "function") {
            mostrarToast(`${lista[0].titulo}: ${lista[0].mensagem}`);
        }
        primeiraCarga = false;
    }

    async function abrirPainel() {
        renderizarLista();
        painel.classList.remove("hidden");
        botao.setAttribute("aria-expanded", "true");
        if (naoLidas === 0) return;

        // Marca como lidas ao abrir; a lista já renderizada mantém o destaque
        // das novas até a próxima atualização.
        const resultado = await enviarJson("/api/notificacoes/lidas", {});
        if (resultado.ok) {
            naoLidas = 0;
            renderizarContador();
        }
    }

    function fecharPainel() {
        painel.classList.add("hidden");
        botao.setAttribute("aria-expanded", "false");
    }

    function montar() {
        botao = document.createElement("button");
        botao.type = "button";
        botao.className = "notif-bell";
        botao.setAttribute("aria-label", "Notificações");
        botao.setAttribute("aria-haspopup", "true");
        botao.setAttribute("aria-expanded", "false");
        botao.innerHTML = `${NOTIFICACOES_ICONE_SINO}<span class="notif-badge hidden"></span>`;
        contador = botao.querySelector(".notif-badge");

        painel = document.createElement("div");
        painel.className = "notif-painel hidden";
        painel.setAttribute("role", "region");
        painel.setAttribute("aria-label", "Notificações");
        painel.innerHTML = `
            <div class="notif-painel-topo"><strong>Notificações</strong></div>
            <ul class="notif-lista"></ul>
        `;

        document.body.appendChild(botao);
        document.body.appendChild(painel);

        botao.addEventListener("click", (evento) => {
            evento.stopPropagation();
            if (painel.classList.contains("hidden")) abrirPainel();
            else fecharPainel();
        });
        document.addEventListener("click", (evento) => {
            if (!painel.classList.contains("hidden") && !painel.contains(evento.target)) fecharPainel();
        });
        document.addEventListener("keydown", (evento) => {
            if (evento.key === "Escape") fecharPainel();
        });
        document.addEventListener("visibilitychange", () => {
            if (!document.hidden) carregar();
        });

        carregar();
        timer = setInterval(carregar, NOTIFICACOES_POLLING_MS);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", montar);
    } else {
        montar();
    }

    // Exposto só pra testes/depuração.
    window.__notificacoes = { recarregar: carregar, parar: () => clearInterval(timer) };
})();
