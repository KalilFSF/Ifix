/* Tela de perfil (frontend/pages/perfil.html).

   Uma única tela para cliente e técnico: o núcleo (foto, dados pessoais,
   endereço/localização, horário e senha) é igual para os dois, porque nada
   disso é atributo de papel — é atributo da conta. O que muda é só o bloco
   de dados profissionais, que aparece quando eh_tecnico é verdadeiro; no
   lugar dele, o cliente vê o convite para virar técnico.

   Consome endpoints que já existiam no backend e nunca tinham sido usados
   por nenhuma tela: PATCH /api/me e GET|PATCH /api/tecnico/perfil. */

const ESCOLARIDADES = ["Ensino médio", "Técnico", "Superior cursando", "Superior completo"];

let usuarioAtual = null;
// Coordenadas capturadas pelo botão "Atualizar minha localização". Só vão
// junto do endereço quando o usuário pediu explicitamente: mandar o que o
// navegador devolveu no load sobrescreveria a localização cadastrada sem
// que ele tivesse pedido nada.
let coordenadasNovas = null;


/* ============== Dados pessoais ============== */

function preencherDadosPessoais(dados) {
    document.getElementById("perfilNome").value = dados.nome || "";
    document.getElementById("perfilTelefone").value = dados.telefone || "";
    document.getElementById("perfilEmail").value = dados.email || "";
    document.getElementById("perfilCpf").value = formatarCpf(dados.cpf);
    renderizarAvatar(dados);
}

function formatarCpf(cpf) {
    if (!cpf || cpf.length !== 11) return cpf || "";
    return `${cpf.slice(0, 3)}.${cpf.slice(3, 6)}.${cpf.slice(6, 9)}-${cpf.slice(9)}`;
}

function renderizarAvatar(dados) {
    document.getElementById("perfilAvatar").innerHTML =
        renderizarAvatarHTML(dados.nome, dados.foto_perfil, "avatar-lg");
}

function iniciarDadosPessoais() {
    document.getElementById("formDados").addEventListener("submit", async (evento) => {
        evento.preventDefault();
        const botao = evento.target.querySelector("button[type=submit]");
        botao.disabled = true;

        const resultado = await enviarJson("/api/me", {
            nome: document.getElementById("perfilNome").value.trim(),
            telefone: document.getElementById("perfilTelefone").value.trim(),
        }, "PATCH");

        botao.disabled = false;

        if (!resultado.ok) {
            mostrarErro(resultado.erro, "mensagemDados");
            return;
        }

        usuarioAtual = { ...usuarioAtual, ...resultado.dados.usuario };
        renderizarAvatar(usuarioAtual);
        limparMensagem("mensagemDados");
        mostrarToast("Dados pessoais atualizados.");
    });
}


/* ============== Foto ============== */

function iniciarFoto() {
    const campo = document.getElementById("perfilFoto");

    campo.addEventListener("change", async () => {
        const arquivo = campo.files[0];
        if (!arquivo) return;

        const corpo = new FormData();
        corpo.append("foto_perfil", arquivo);

        mostrarToast("Enviando foto...");
        const resultado = await enviarFormulario("/api/me/foto", corpo, "PUT");
        // Zera o input pra escolher o MESMO arquivo de novo disparar change
        // (útil quando o primeiro envio falhou).
        campo.value = "";

        if (!resultado.ok) {
            mostrarToast(resultado.erro);
            return;
        }

        usuarioAtual.foto_perfil = resultado.dados.foto_perfil;
        renderizarAvatar(usuarioAtual);
        mostrarToast("Foto de perfil atualizada.");
    });
}


/* ============== Endereço e localização ============== */

async function preencherEndereco(dados) {
    document.getElementById("perfilCep").value = dados.cep || "";
    document.getElementById("perfilBairro").value = dados.bairro || "";
    document.getElementById("perfilEndereco").value = dados.endereco || "";
    document.getElementById("perfilNumero").value = dados.numero || "";
    document.getElementById("perfilComplemento").value = dados.complemento || "";

    const selectEstado = document.getElementById("perfilEstado");
    const selectCidade = document.getElementById("perfilCidade");

    await carregarEstados(selectEstado);
    if (dados.estado) {
        selectEstado.value = dados.estado;
        await carregarCidades(dados.estado, selectCidade);
        if (dados.cidade) selectCidade.value = dados.cidade;
    }

    atualizarStatusLocalizacao(dados);
}

function atualizarStatusLocalizacao(dados) {
    const status = document.getElementById("perfilLocalizacaoStatus");
    const temCoordenada = dados.latitude !== null && dados.latitude !== undefined;

    if (coordenadasNovas) {
        status.textContent = "Nova localização capturada — salve o endereço para aplicá-la.";
        return;
    }
    status.textContent = temCoordenada
        ? `Localização cadastrada (${Number(dados.latitude).toFixed(4)}, ${Number(dados.longitude).toFixed(4)}).`
        : "Sem localização cadastrada — você fica de fora da busca por proximidade.";
}

function iniciarEndereco() {
    const selectEstado = document.getElementById("perfilEstado");
    const selectCidade = document.getElementById("perfilCidade");
    const campoCep = document.getElementById("perfilCep");

    selectEstado.addEventListener("change", () => {
        if (selectEstado.value) carregarCidades(selectEstado.value, selectCidade);
    });

    // Busca de CEP, mesmo comportamento do cadastro (ViaCEP).
    campoCep.addEventListener("input", async () => {
        const cep = campoCep.value.replace(/\D/g, "");
        if (cep.length !== 8) return;

        let dados;
        try {
            const resposta = await fetch(`https://viacep.com.br/ws/${cep}/json/`);
            dados = await resposta.json();
        } catch (erro) {
            console.error("[perfil] falha ao consultar o ViaCEP", erro);
            mostrarErro("Não foi possível buscar o CEP agora. Preencha o endereço manualmente.", "mensagemEndereco");
            return;
        }

        if (dados.erro) {
            mostrarErro("CEP não encontrado. Confira o número digitado.", "mensagemEndereco");
            return;
        }

        limparMensagem("mensagemEndereco");
        await carregarEstados(selectEstado);
        selectEstado.value = dados.uf;
        await carregarCidades(dados.uf, selectCidade);
        selectCidade.value = dados.localidade;
        document.getElementById("perfilBairro").value = dados.bairro || "";
        document.getElementById("perfilEndereco").value = dados.logradouro || "";
    });

    document.getElementById("btnAtualizarLocalizacao").addEventListener("click", async (evento) => {
        const botao = evento.currentTarget;
        botao.disabled = true;
        botao.textContent = "Capturando...";

        const coordenadas = await obterCoordenadas();

        botao.disabled = false;
        botao.textContent = "Atualizar minha localização";

        if (!coordenadas) {
            mostrarErro(
                "Não foi possível obter sua localização. Permita o acesso no navegador e tente de novo.",
                "mensagemEndereco",
            );
            return;
        }

        coordenadasNovas = coordenadas;
        limparMensagem("mensagemEndereco");
        atualizarStatusLocalizacao(usuarioAtual);
        mostrarToast("Localização capturada. Salve o endereço para aplicar.");
    });

    document.getElementById("formEndereco").addEventListener("submit", async (evento) => {
        evento.preventDefault();
        const botao = evento.target.querySelector("button[type=submit]");
        botao.disabled = true;

        const corpo = {
            cep: campoCep.value.trim(),
            estado: selectEstado.value,
            cidade: selectCidade.value,
            bairro: document.getElementById("perfilBairro").value.trim(),
            endereco: document.getElementById("perfilEndereco").value.trim(),
            numero: document.getElementById("perfilNumero").value.trim(),
            complemento: document.getElementById("perfilComplemento").value.trim(),
        };
        if (coordenadasNovas) {
            corpo.latitude = coordenadasNovas.latitude;
            corpo.longitude = coordenadasNovas.longitude;
        }

        const resultado = await enviarJson("/api/me", corpo, "PATCH");
        botao.disabled = false;

        if (!resultado.ok) {
            mostrarErro(resultado.erro, "mensagemEndereco");
            return;
        }

        usuarioAtual = { ...usuarioAtual, ...resultado.dados.usuario };
        coordenadasNovas = null;
        atualizarStatusLocalizacao(usuarioAtual);
        limparMensagem("mensagemEndereco");
        mostrarToast("Endereço atualizado.");
    });
}


/* ============== Horário de atendimento ============== */

function iniciarHorario(dados) {
    const elInicio = document.getElementById("horarioInicio");
    const elFim = document.getElementById("horarioFim");
    const elBotao = document.getElementById("horarioSalvarBtn");

    elInicio.value = dados.horario_inicio_atendimento || "08:00";
    elFim.value = dados.horario_fim_atendimento || "18:00";

    elBotao.addEventListener("click", async () => {
        if (!elInicio.value || !elFim.value) {
            mostrarToast("Preencha os dois horários.");
            return;
        }
        if (elInicio.value === elFim.value) {
            mostrarToast("O horário de início e o de término não podem ser iguais.");
            return;
        }

        elBotao.disabled = true;
        const resultado = await enviarJson("/api/me/horario-atendimento", {
            horario_inicio_atendimento: elInicio.value,
            horario_fim_atendimento: elFim.value,
        }, "PUT");
        elBotao.disabled = false;

        mostrarToast(resultado.ok ? "Horário de atendimento atualizado." : resultado.erro);
    });
}


/* ============== Dados profissionais (só técnico) ============== */

function preencherPerfilTecnico(dados) {
    const secaoTecnico = document.getElementById("secaoTecnico");
    const secaoVirar = document.getElementById("secaoVirarTecnico");

    if (!dados.eh_tecnico || !dados.perfil) {
        secaoVirar.classList.remove("hidden");
        return;
    }

    secaoTecnico.classList.remove("hidden");

    const perfil = dados.perfil;
    document.getElementById("tecEspecialidade").value = perfil.especialidade || "";
    document.getElementById("tecCursoSuperior").value = perfil.curso_superior || "";
    document.getElementById("tecRegiao").value = perfil.regiao_atendimento || "";
    document.getElementById("tecCursos").value = perfil.cursos_experiencias || "";
    document.getElementById("tecEspecializacoes").value = perfil.especializacoes || "";
    document.getElementById("tecValorMedio").value = perfil.valor_medio ?? "";

    const selectEscolaridade = document.getElementById("tecEscolaridade");
    selectEscolaridade.value = ESCOLARIDADES.includes(perfil.escolaridade) ? perfil.escolaridade : "";

    document.getElementById("perfilNotaMedia").textContent = perfil.total_avaliacoes
        ? `Nota média ${Number(perfil.nota_media).toFixed(1)} em ${perfil.total_avaliacoes} avaliação(ões).`
        : "Você ainda não recebeu avaliações.";

    renderizarDiplomas(dados.diplomas || []);
}

function renderizarDiplomas(diplomas) {
    const container = document.getElementById("perfilDiplomas");
    if (!diplomas.length) {
        container.innerHTML = `<p class="perfil-ajuda">Nenhum diploma enviado.</p>`;
        return;
    }
    container.innerHTML = `
        <div class="input-group">
            <label>Diplomas enviados</label>
            <ul class="perfil-diplomas">
                ${diplomas.map((diploma, indice) => `
                    <li><a href="${escaparHtml(diploma.arquivo)}" target="_blank" rel="noopener">Diploma ${indice + 1}</a></li>
                `).join("")}
            </ul>
        </div>
    `;
}

function iniciarPerfilTecnico() {
    const formulario = document.getElementById("formTecnico");
    if (!formulario) return;

    formulario.addEventListener("submit", async (evento) => {
        evento.preventDefault();
        const botao = evento.target.querySelector("button[type=submit]");
        botao.disabled = true;

        const resultado = await enviarJson("/api/tecnico/perfil", {
            especialidade: document.getElementById("tecEspecialidade").value.trim(),
            escolaridade: document.getElementById("tecEscolaridade").value,
            curso_superior: document.getElementById("tecCursoSuperior").value.trim(),
            regiao_atendimento: document.getElementById("tecRegiao").value.trim(),
            cursos_experiencias: document.getElementById("tecCursos").value.trim(),
            especializacoes: document.getElementById("tecEspecializacoes").value.trim(),
            valor_medio: document.getElementById("tecValorMedio").value.trim(),
        }, "PATCH");

        botao.disabled = false;

        if (!resultado.ok) {
            mostrarErro(resultado.erro, "mensagemTecnico");
            return;
        }

        limparMensagem("mensagemTecnico");
        mostrarToast("Dados profissionais atualizados.");
    });
}


/* ============== Senha ============== */

function iniciarSenha() {
    document.getElementById("formSenha").addEventListener("submit", async (evento) => {
        evento.preventDefault();

        const atual = document.getElementById("senhaAtual");
        const nova = document.getElementById("senhaNova");
        const confirmar = document.getElementById("senhaConfirmar");
        const botao = evento.target.querySelector("button[type=submit]");

        botao.disabled = true;
        const resultado = await enviarJson("/api/me/senha", {
            senha_atual: atual.value,
            nova_senha: nova.value,
            confirmar_senha: confirmar.value,
        });
        botao.disabled = false;

        if (!resultado.ok) {
            mostrarErro(resultado.erro, "mensagemSenha");
            return;
        }

        atual.value = "";
        nova.value = "";
        confirmar.value = "";
        limparMensagem("mensagemSenha");
        mostrarToast("Senha alterada. Ela já vale no próximo login.");
    });
}


/* ============== Bootstrap ============== */

(async function iniciar() {
    iniciarSidebarMobile();

    // O perfil é da conta, não do papel — mas os chips da sidebar precisam
    // refletir o modo certo, então o modo ativo segue o papel do usuário.
    const dados = await iniciarRoleChips("cliente");
    if (!dados) return;

    usuarioAtual = dados;

    preencherDadosPessoais(dados);
    await preencherEndereco(dados);
    iniciarHorario(dados);
    preencherPerfilTecnico(dados);

    iniciarDadosPessoais();
    iniciarFoto();
    iniciarEndereco();
    iniciarPerfilTecnico();
    iniciarSenha();
})();
