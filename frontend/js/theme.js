/* Tema claro/escuro compartilhado por TODAS as páginas do iFix.
   O tema em si é feito 100% em CSS via a classe "light" na <html> (ver as
   variáveis --bg-*, --text-*, --border-* em style.css); aqui só ligamos/
   desligamos essa classe e lembramos a escolha em localStorage.

   Este arquivo é carregado no <head> (sem defer/async, ver index.html,
   cadastro.html, cliente-home.html e tecnico-home.html) de propósito: a
   parte que aplica o tema salvo roda de forma síncrona antes do <body> ser
   pintado, então a página nunca "pisca" no tema errado antes de trocar.
   O binding dos switches (que depende do <body> já existir) só roda depois
   do DOM estar pronto. */
(function () {
    const STORAGE_KEY = "theme";

    function temaClaroSalvo() {
        return localStorage.getItem(STORAGE_KEY) === "light";
    }

    function aplicarTema(isLight) {
        document.documentElement.classList.toggle("light", isLight);
    }

    // Roda imediatamente ao carregar o <script>, antes do body existir.
    aplicarTema(temaClaroSalvo());

    function iniciarSwitches() {
        const toggles = document.querySelectorAll(".themeToggle");
        if (!toggles.length) return;

        function definirTema(isLight) {
            aplicarTema(isLight);
            localStorage.setItem(STORAGE_KEY, isLight ? "light" : "dark");

            // Pode ter mais de um switch de tema na mesma página (um por
            // card); mantém todos sincronizados com o mesmo estado.
            toggles.forEach(toggle => {
                toggle.checked = isLight;
            });
        }

        definirTema(temaClaroSalvo());

        toggles.forEach(toggle => {
            toggle.addEventListener("change", () => definirTema(toggle.checked));
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", iniciarSwitches);
    } else {
        iniciarSwitches();
    }
})();
