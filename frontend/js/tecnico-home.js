/* Busca os dados do técnico logado (GET /api/me) e preenche a página
   (nome, foto, especialidade, região de atendimento e nº de diplomas). */

(async function () {
    const resposta = await fetch("/api/me");

    if (!resposta.ok) {
        window.location.href = "/";
        return;
    }

    const dados = await resposta.json();

    document.getElementById("nomeUsuario").textContent = `Olá, ${dados.nome}!`;

    if (dados.foto_perfil) {
        const foto = document.getElementById("fotoPerfil");
        foto.src = dados.foto_perfil;
        foto.style.display = "block";
    }

    let detalhes = `Sua conta de técnico foi criada com sucesso `
        + `(especialidade: ${dados.especialidade}, atendimento em ${dados.regiao_atendimento}). `;

    if (dados.diplomas_count > 0) {
        detalhes += `${dados.diplomas_count} diploma(s)/certificado(s) enviado(s). `;
    }

    detalhes += "Em breve você poderá receber chamados, enviar orçamentos e registrar serviços por aqui.";

    document.getElementById("detalhesTecnico").textContent = detalhes;

    const perfilResposta = await fetch("/api/tecnico/perfil");
    if (perfilResposta.ok) {
        const perfilDados = await perfilResposta.json();
        if (perfilDados.ok) {
            const perfilTexto = `Especialidade: ${perfilDados.perfil.especialidade} | Região: ${perfilDados.perfil.regiao_atendimento}`;
            document.getElementById("detalhesTecnico").textContent = perfilTexto;
        }
    }

    const lista = document.getElementById("listaServicos");
    const listaAtendimentos = document.getElementById("listaAtendimentos");

    async function carregarServicos() {
        const respostaServicos = await fetch("/api/servicos?status=aberto");
        const servicos = await respostaServicos.json();

        if (!lista) return;
        lista.innerHTML = "";

        if (!servicos.length) {
            lista.innerHTML = "<li>Nenhum chamado aberto no momento.</li>";
            return;
        }

        servicos.forEach(servico => {
            const item = document.createElement("li");
            item.innerHTML = `
                <strong>${servico.titulo}</strong><br>
                ${servico.descricao}<br>
                Categoria: ${servico.categoria}<br>
                Status: ${servico.status}<br>
                Valor estimado: R$ ${Number(servico.preco_estimado || 0).toFixed(2)}
                <button data-id="${servico.id}" class="primary-btn" style="margin-top:8px;">Aceitar chamado</button>
            `;
            lista.appendChild(item);
        });
    }

    async function carregarAtendimentos() {
        if (!listaAtendimentos) return;
        const resposta = await fetch("/api/atendimentos");
        const atendimentos = await resposta.json();
        listaAtendimentos.innerHTML = "";

        if (!atendimentos.length) {
            listaAtendimentos.innerHTML = "<li>Nenhum orçamento enviado.</li>";
            return;
        }

        atendimentos.forEach(atendimento => {
            const item = document.createElement("li");
            item.innerHTML = `<strong>${atendimento.titulo}</strong><br>${atendimento.descricao}<br>Status: ${atendimento.status}<br>Orçamento: R$ ${Number(atendimento.valor_orcamento || 0).toFixed(2)}`;
            listaAtendimentos.appendChild(item);
        });
    }

    lista.addEventListener("click", async (event) => {
        const botao = event.target.closest("button[data-id]");
        if (!botao) return;

        const id = botao.getAttribute("data-id");
        const respostaAceite = await fetch(`/api/servicos/${id}/aceitar`, { method: "POST" });
        const resultado = await respostaAceite.json();

        if (resultado.ok) {
            carregarServicos();
        }
    });

    carregarServicos();
    carregarAtendimentos();
})();
