/* Busca os dados do usuário logado (GET /api/me) e preenche a página.
   Sem isso, a página não saberia o nome do cliente — antes o Jinja fazia
   isso no servidor ({{ current_user.nome }}), agora é o JS que faz no navegador. */

(async function () {
    const resposta = await fetch("/api/me");

    if (!resposta.ok) {
        window.location.href = "/";
        return;
    }

    const dados = await resposta.json();
    document.getElementById("nomeUsuario").textContent = `Olá, ${dados.nome}!`;

    const lista = document.getElementById("listaServicos");
    const listaTecnicos = document.getElementById("listaTecnicos");
    const listaAtendimentos = document.getElementById("listaAtendimentos");
    const mensagem = document.getElementById("mensagemServico");
    const form = document.getElementById("servicoForm");

    async function carregarServicos() {
        const respostaServicos = await fetch("/api/servicos");
        const servicos = await respostaServicos.json();

        if (!lista) return;
        lista.innerHTML = "";

        if (!servicos.length) {
            lista.innerHTML = "<li>Nenhum chamado registrado ainda.</li>";
            return;
        }

        servicos.forEach(servico => {
            const item = document.createElement("li");
            item.innerHTML = `<strong>${servico.titulo}</strong> <br> ${servico.descricao} <br> Categoria: ${servico.categoria} <br> Status: ${servico.status} <br> Valor estimado: R$ ${Number(servico.preco_estimado || 0).toFixed(2)}`;
            lista.appendChild(item);
        });
    }

    async function carregarTecnicos() {
        if (!listaTecnicos) return;
        const resposta = await fetch("/api/tecnicos");
        const tecnicos = await resposta.json();
        listaTecnicos.innerHTML = "";

        if (!tecnicos.length) {
            listaTecnicos.innerHTML = "<li>Nenhum técnico cadastrado ainda.</li>";
            return;
        }

        tecnicos.forEach(tecnico => {
            const item = document.createElement("li");
            item.innerHTML = `<strong>${tecnico.nome}</strong><br>${tecnico.cidade || "Cidade não informada"} - ${tecnico.estado || "Estado não informado"}`;
            listaTecnicos.appendChild(item);
        });
    }

    async function carregarAtendimentos() {
        if (!listaAtendimentos) return;
        const resposta = await fetch("/api/atendimentos");
        const atendimentos = await resposta.json();
        listaAtendimentos.innerHTML = "";

        if (!atendimentos.length) {
            listaAtendimentos.innerHTML = "<li>Nenhum atendimento registrado.</li>";
            return;
        }

        atendimentos.forEach(atendimento => {
            const item = document.createElement("li");
            item.innerHTML = `<strong>${atendimento.titulo}</strong><br>${atendimento.descricao}<br>Status: ${atendimento.status}<br>Orçamento: R$ ${Number(atendimento.valor_orcamento || 0).toFixed(2)}`;
            listaAtendimentos.appendChild(item);
        });
    }

    if (form) {
        form.addEventListener("submit", async (event) => {
            event.preventDefault();
            const payload = Object.fromEntries(new FormData(form));
            payload.preco_estimado = payload.preco_estimado ? Number(payload.preco_estimado) : 0;

            const respostaEnvio = await fetch("/api/servicos", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            const resultado = await respostaEnvio.json();
            if (resultado.ok) {
                mensagem.textContent = "Chamado criado com sucesso!";
                mensagem.style.color = "green";
                form.reset();
                carregarServicos();
            } else {
                mensagem.textContent = resultado.erro || "Não foi possível criar o chamado.";
                mensagem.style.color = "crimson";
            }
        });
    }

    carregarServicos();
    carregarTecnicos();
    carregarAtendimentos();
})();
