/* Helper de escape para interpolação em template literal + innerHTML.

   Todo o front renderiza com `elemento.innerHTML = \`...${dado}...\``, e boa
   parte desses dados é texto livre digitado por outro usuário (título e
   descrição do chamado, nome do cliente, comentário de avaliação, laudo do
   técnico). Sem escapar, um "<img src=x onerror=...>" salvo na descrição
   executaria na tela de quem abrisse o chamado.

   Uso: escaparHtml(valor) em qualquer campo vindo da API que tenha origem
   em digitação de usuário. Não use em valores que você mesmo gerou
   (códigos, classes CSS, números já formatados). */

const MAPA_ESCAPE_HTML = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
};

function escaparHtml(texto) {
    if (texto === null || texto === undefined) return "";
    return String(texto).replace(/[&<>"']/g, caractere => MAPA_ESCAPE_HTML[caractere]);
}
