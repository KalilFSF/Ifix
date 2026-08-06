/* Funções auxiliares de busca de estados/cidades na API do IBGE.
   O valor de cada <option> de estado é a sigla (ex: "SP"), que também
   é aceita pela própria API do IBGE para buscar os municípios. */

async function carregarEstados(selectEstado) {
    selectEstado.innerHTML = `<option value="">Carregando estados...</option>`;

    const resposta = await fetch("https://servicodados.ibge.gov.br/api/v1/localidades/estados?orderBy=nome");
    const estados = await resposta.json();

    selectEstado.innerHTML = `<option value="">Selecione</option>`;

    estados.forEach(estado => {
        const option = document.createElement("option");
        option.value = estado.sigla;
        option.textContent = estado.nome;
        selectEstado.appendChild(option);
    });
}

async function carregarCidades(estadoSigla, selectCidade) {
    selectCidade.innerHTML = `<option value="">Carregando cidades...</option>`;

    const resposta = await fetch(`https://servicodados.ibge.gov.br/api/v1/localidades/estados/${estadoSigla}/municipios?orderBy=nome`);
    const cidades = await resposta.json();

    selectCidade.innerHTML = `<option value="">Selecione</option>`;

    cidades.forEach(cidade => {
        const option = document.createElement("option");
        option.value = cidade.nome;
        option.textContent = cidade.nome;
        selectCidade.appendChild(option);
    });
}
