/* Camada única de acesso à API.

   Antes disso, cada tela escrevia `await fetch(...)` cru e tratava (ou não)
   o erro do seu jeito. O padrão mais comum era
   `const lista = resposta.ok ? await resposta.json() : []`, que transforma
   uma falha do servidor em "não há nada" — visualmente idêntico a um estado
   legítimo, e por isso invisível pro usuário e pra quem for depurar.

   Aqui todo erro vira um objeto com a mesma forma:

       { ok, status, dados, erro, falhaDeRede, naoAutenticado }

   `erro` é sempre uma frase pronta pra mostrar na tela (a do servidor
   quando existe, uma genérica por status quando não). Quem chama decide
   entre toast, mensagem inline ou estado de erro no container — mas nunca
   mais some sem deixar rastro: toda falha também é registrada no console. */

const MENSAGENS_POR_STATUS = {
    400: "Alguns dados não foram aceitos. Revise o que foi preenchido.",
    401: "Sua sessão expirou. Entre novamente para continuar.",
    403: "Você não tem permissão para esta ação.",
    404: "Não encontramos o que você procura.",
    409: "Esta ação já foi feita ou não é mais válida.",
    413: "O arquivo enviado é grande demais.",
};

const MENSAGEM_ERRO_SERVIDOR = "O servidor não respondeu como esperado. Tente novamente em instantes.";
const MENSAGEM_ERRO_REDE = "Sem conexão com o servidor. Verifique sua internet e tente de novo.";
const MENSAGEM_ERRO_GENERICA = "Não foi possível completar a ação. Tente novamente.";

function mensagemPorStatus(status) {
    if (MENSAGENS_POR_STATUS[status]) return MENSAGENS_POR_STATUS[status];
    if (status >= 500) return MENSAGEM_ERRO_SERVIDOR;
    return MENSAGEM_ERRO_GENERICA;
}

/* Base de tudo. Nunca lança: o erro vem no retorno, pra quem chama não
   precisar de try/catch só pra não travar um botão em "Enviando...". */
async function requisitar(url, opcoes = {}) {
    let resposta;
    try {
        resposta = await fetch(url, opcoes);
    } catch (erro) {
        console.error(`[api] falha de rede em ${opcoes.method || "GET"} ${url}`, erro);
        return {
            ok: false,
            status: 0,
            dados: null,
            erro: MENSAGEM_ERRO_REDE,
            falhaDeRede: true,
            naoAutenticado: false,
        };
    }

    // Um 500 do Flask devolve HTML, não JSON — por isso o parse é protegido
    // em vez de `await resposta.json()` direto, que lançaria aqui.
    let dados = null;
    try {
        const tipo = resposta.headers.get("content-type") || "";
        if (tipo.includes("application/json")) dados = await resposta.json();
    } catch (erro) {
        console.error(`[api] resposta de ${url} não é JSON válido`, erro);
    }

    const erroDoServidor = dados && typeof dados === "object" ? dados.erro : null;

    if (resposta.ok) {
        // Alguns endpoints antigos devolvem {ok:false} com HTTP 200.
        if (dados && typeof dados === "object" && dados.ok === false) {
            console.error(`[api] ${url} respondeu ok:false — ${erroDoServidor}`);
            return {
                ok: false,
                status: resposta.status,
                dados,
                erro: erroDoServidor || MENSAGEM_ERRO_GENERICA,
                falhaDeRede: false,
                naoAutenticado: false,
            };
        }
        return { ok: true, status: resposta.status, dados, erro: null, falhaDeRede: false, naoAutenticado: false };
    }

    const erro = erroDoServidor || mensagemPorStatus(resposta.status);
    console.error(`[api] ${resposta.status} em ${opcoes.method || "GET"} ${url} — ${erro}`);
    return {
        ok: false,
        status: resposta.status,
        dados,
        erro,
        falhaDeRede: false,
        naoAutenticado: resposta.status === 401,
    };
}

function obterJson(url) {
    return requisitar(url);
}

/* Para os endpoints que devolvem array puro (sem envelope {ok}), como
   GET /api/servicos/<id>/avaliacoes e /historico. `lista` é sempre um
   array — mas `ok:false` diz que ele está vazio por falha, não por não
   haver dados, que é exatamente a distinção que o front não tinha. */
async function obterLista(url) {
    const resultado = await requisitar(url);
    const lista = Array.isArray(resultado.dados) ? resultado.dados : [];
    return { ...resultado, lista };
}

function enviarJson(url, corpo, metodo = "POST") {
    return requisitar(url, {
        method: metodo,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(corpo),
    });
}

function enviarFormulario(url, formData, metodo = "POST") {
    return requisitar(url, { method: metodo, body: formData });
}
