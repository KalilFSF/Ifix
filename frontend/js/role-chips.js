/* Chips Cliente | Técnico na sidebar.
   - Sem perfil técnico: chip Técnico abre o modal de conversão.
   - Com perfil técnico: chips alternam entre /cliente/home e /tecnico/home. */

async function iniciarRoleChips(modoAtivo) {
    const indicador = document.querySelector(".role-indicator");
    if (!indicador) return null;

    // Só 401 significa "não está logado". Antes, QUALQUER falha (inclusive
    // uma oscilação de rede) mandava o usuário pro login sem mensagem, como
    // se a sessão tivesse expirado — e ele perdia o que estava fazendo.
    const resultado = await obterJson("/api/me");
    if (!resultado.ok) {
        if (resultado.naoAutenticado) {
            window.location.href = "/";
            return null;
        }
        mostrarToast(resultado.erro);
        return null;
    }

    const dados = resultado.dados;
    const ehTecnico = Boolean(dados.eh_tecnico);

    if (modoAtivo === "cliente") {
        if (ehTecnico) {
            const chipTecnico = document.getElementById("chipTornarTecnico");
            if (chipTecnico) {
                chipTecnico.title = "Ir para o Painel do Técnico";
                chipTecnico.addEventListener("click", () => {
                    window.location.href = "/tecnico/home";
                });
            }
            const overlay = document.getElementById("tornarTecnicoOverlay");
            if (overlay) overlay.remove();
        } else {
            iniciarModalTornarTecnico();
        }
    } else if (modoAtivo === "tecnico") {
        indicador.setAttribute("aria-label", "Perfil da conta: Técnico");
        indicador.innerHTML = `
            <a href="/cliente/home" class="role-chip role-chip-link" title="Usar o iFix como cliente.">Cliente</a>
            <span class="role-chip role-chip-active">Técnico</span>
        `;
    }

    return dados;
}

function iniciarModalTornarTecnico() {
    const chip = document.getElementById("chipTornarTecnico");
    const overlay = document.getElementById("tornarTecnicoOverlay");
    const btnFechar = document.getElementById("tornarTecnicoClose");
    if (!chip || !overlay || !btnFechar) return;

    chip.addEventListener("click", () => overlay.classList.remove("hidden"));
    btnFechar.addEventListener("click", () => overlay.classList.add("hidden"));
    overlay.addEventListener("click", (evento) => {
        if (evento.target === overlay) overlay.classList.add("hidden");
    });
}
