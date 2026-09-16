/* Funções auxiliares de busca de estados/cidades na API do IBGE.
   O valor de cada <option> de estado é a sigla (ex: "SP"), que também
   é aceita pela própria API do IBGE para buscar os municípios.

   O IBGE é um serviço externo e fora do nosso controle: quando ele não
   responde, o <select> precisa dizer isso e deixar o usuário tentar de
   novo — antes ele ficava preso em "Carregando estados..." para sempre. */

async function preencherSelect(select, url, rotuloCarregando, rotuloErro, mapear) {
    select.innerHTML = `<option value="">${rotuloCarregando}</option>`;
    select.disabled = true;

    let itens;
    try {
        const resposta = await fetch(url);
        if (!resposta.ok) throw new Error(`IBGE respondeu ${resposta.status}`);
        itens = await resposta.json();
    } catch (erro) {
        console.error(`[ibge] falha ao carregar ${url}`, erro);
        select.innerHTML = `<option value="">${rotuloErro}</option>`;
        select.disabled = false;
        return false;
    }

    select.innerHTML = `<option value="">Selecione</option>`;
    itens.forEach(item => {
        const option = document.createElement("option");
        const { valor, texto } = mapear(item);
        option.value = valor;
        option.textContent = texto;
        select.appendChild(option);
    });
    select.disabled = false;
    return true;
}

async function carregarEstados(selectEstado) {
    return preencherSelect(
        selectEstado,
        "https://servicodados.ibge.gov.br/api/v1/localidades/estados?orderBy=nome",
        "Carregando estados...",
        "Não foi possível carregar os estados — tente de novo",
        estado => ({ valor: estado.sigla, texto: estado.nome }),
    );
}

async function carregarCidades(estadoSigla, selectCidade) {
    return preencherSelect(
        selectCidade,
        `https://servicodados.ibge.gov.br/api/v1/localidades/estados/${estadoSigla}/municipios?orderBy=nome`,
        "Carregando cidades...",
        "Não foi possível carregar as cidades — tente de novo",
        cidade => ({ valor: cidade.nome, texto: cidade.nome }),
    );
}
