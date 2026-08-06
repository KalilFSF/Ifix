/* Alterna tema claro/escuro em qualquer página (carregado por base.html).
   O tema em si é feito 100% em CSS via a classe "light" na <html>
   (ver as variáveis --bg-*, --text-* em static/css/style.css);
   aqui só ligamos/desligamos essa classe e lembramos a escolha. */
(function () {
    const toggles = document.querySelectorAll(".themeToggle");

    function setTheme(isLight) {
        document.documentElement.classList.toggle("light", isLight);
        localStorage.setItem("theme", isLight ? "light" : "dark");

        // Pode ter mais de um switch de tema na mesma página (um por card);
        // mantém todos sincronizados com o mesmo estado.
        toggles.forEach(toggle => {
            toggle.checked = isLight;
        });
    }

    const saved = localStorage.getItem("theme");
    setTheme(saved === "light");

    toggles.forEach(toggle => {
        toggle.addEventListener("change", () => setTheme(toggle.checked));
    });
})();
