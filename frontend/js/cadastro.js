/* Lógica da tela de cadastro: alternar cliente/técnico, aplicar máscaras
   (telefone, CPF, CEP), buscar endereço pelo CEP (ViaCEP), popular os
   selects de estado/cidade (IBGE, via as funções de estadosCidades.js —
   por isso esse outro arquivo precisa ser carregado ANTES deste no HTML)
   e enviar os dois formulários via fetch pra API do backend. */

/* ==================================================
   CONSTANTES
================================================== */

const tipoConta = document.getElementById("tipoConta");
const clienteCadastro = document.getElementById("clienteCadastro");
const tecnicoCadastro = document.getElementById("tecnicoCadastro");

const typeButtons = document.querySelectorAll(".type-option");
const voltarButtons = document.querySelectorAll(".voltar");


/* ==================================================
   ALTERNÂNCIA CLIENTE / TÉCNICO
================================================== */

function abrirCadastro(tipo) {
    tipoConta.classList.add("hidden");

    if (tipo === "cliente") {
        clienteCadastro.classList.remove("hidden");
    } else {
        tecnicoCadastro.classList.remove("hidden");
    }
}

function voltarInicio() {
    clienteCadastro.classList.add("hidden");
    tecnicoCadastro.classList.add("hidden");
    tipoConta.classList.remove("hidden");
}

typeButtons.forEach(button => {
    button.addEventListener("click", () => abrirCadastro(button.dataset.type));
});

voltarButtons.forEach(button => {
    button.addEventListener("click", voltarInicio);
});


/* ==================================================
   MÁSCARAS
================================================== */

function aplicarMascaraTelefone(input) {
    let value = input.value.replace(/\D/g, "");

    if (value.length > 13) value = value.slice(0, 13);

    value = value.replace(/^(\d{2})(\d)/, "+$1 ($2");
    value = value.replace(/^(\+\d{2}) \((\d{2})(\d)/, "$1 ($2) $3");
    value = value.replace(/(\d{5})(\d)/, "$1-$2");

    input.value = value;
}

function aplicarMascaraCpf(input) {
    let value = input.value.replace(/\D/g, "");

    if (value.length > 11) value = value.slice(0, 11);

    value = value.replace(/(\d{3})(\d)/, "$1.$2");
    value = value.replace(/(\d{3})(\d)/, "$1.$2");
    value = value.replace(/(\d{3})(\d{1,2})$/, "$1-$2");

    input.value = value;
}

function aplicarMascaraCep(input) {
    let value = input.value.replace(/\D/g, "");

    if (value.length > 8) value = value.slice(0, 8);

    input.value = value.replace(/(\d{5})(\d)/, "$1-$2");
}

document.querySelectorAll(".telefone").forEach(input => {
    input.addEventListener("input", () => aplicarMascaraTelefone(input));
});

document.querySelectorAll(".cpf").forEach(input => {
    input.addEventListener("input", () => aplicarMascaraCpf(input));
});


/* ==================================================
   PAÍS -> HABILITA/DESABILITA ENDEREÇO E CARREGA ESTADOS
================================================== */

/* Só o Brasil tem CEP/IBGE pra autocompletar; "Outro" país limpa e
   desabilita os campos de endereço (eles ficam opcionais no back-end
   também, ver _validar_dados_comuns em routes.py). */
function desativarEndereco(form) {
    const estadoSelect = form.querySelector(".estado");
    const cidadeSelect = form.querySelector(".cidade");
    const camposEndereco = form.querySelectorAll(".endereco");

    estadoSelect.innerHTML = `<option value="">Selecione</option>`;
    cidadeSelect.innerHTML = `<option value="">Selecione o estado primeiro</option>`;

    camposEndereco.forEach(campo => {
        campo.value = "";
        campo.disabled = true;
        campo.required = false;
    });
}

async function ativarEndereco(form) {
    const estadoSelect = form.querySelector(".estado");
    const camposEndereco = form.querySelectorAll(".endereco");

    camposEndereco.forEach(campo => {
        campo.disabled = false;
        campo.required = true;
    });

    await carregarEstados(estadoSelect);
}

document.querySelectorAll(".pais").forEach(paisSelect => {
    paisSelect.addEventListener("change", () => {
        const form = paisSelect.closest("form");

        if (paisSelect.value === "Outro") {
            desativarEndereco(form);
        } else if (paisSelect.value === "Brasil") {
            ativarEndereco(form);
        }
    });
});

document.querySelectorAll(".estado").forEach(estadoSelect => {
    estadoSelect.addEventListener("change", async () => {
        const form = estadoSelect.closest("form");
        const cidadeSelect = form.querySelector(".cidade");

        if (!estadoSelect.value) {
            cidadeSelect.innerHTML = `<option value="">Selecione o estado primeiro</option>`;
            return;
        }

        await carregarCidades(estadoSelect.value, cidadeSelect);
    });
});


/* ==================================================
   BUSCA AUTOMÁTICA DE CEP (ViaCEP)
================================================== */

/* Ao digitar um CEP válido (8 dígitos), busca o endereço na API pública
   ViaCEP e preenche estado/cidade/bairro/rua sozinho. ViaCEP devolve o
   estado como sigla (dados.uf, ex: "SP"), que já é o mesmo formato usado
   nos <option value> carregados pelo IBGE — por isso dá pra usar
   estadoSelect.value = dados.uf direto, sem precisar converter nada. */
document.querySelectorAll(".cep").forEach(input => {

    input.addEventListener("input", async () => {

        aplicarMascaraCep(input);

        const cep = input.value.replace(/\D/g, "");
        if (cep.length !== 8) return;

        const form = input.closest("form");

        const paisSelect = form.querySelector(".pais");
        const estadoSelect = form.querySelector(".estado");
        const cidadeSelect = form.querySelector(".cidade");
        const bairroInput = form.querySelector(".bairro");
        const ruaInput = form.querySelector(".rua");
        const camposEndereco = form.querySelectorAll(".endereco");

        try {

            const resposta = await fetch(`https://viacep.com.br/ws/${cep}/json/`);
            const dados = await resposta.json();

            if (dados.erro) {
                alert("CEP não encontrado.");
                return;
            }

            paisSelect.value = "Brasil";

            camposEndereco.forEach(campo => {
                campo.disabled = false;
                campo.required = true;
            });

            await carregarEstados(estadoSelect);
            estadoSelect.value = dados.uf;

            await carregarCidades(dados.uf, cidadeSelect);

            const cidadeOption = [...cidadeSelect.options].find(
                option => option.textContent === dados.localidade
            );
            if (cidadeOption) {
                cidadeSelect.value = cidadeOption.value;
            }

            bairroInput.value = dados.bairro || "";
            ruaInput.value = dados.logradouro || "";

        } catch {
            alert("Não foi possível buscar o CEP.");
        }

    });

});


/* ==================================================
   VALIDAÇÃO DA DATA DE NASCIMENTO
================================================== */

/* O min/max só limita o seletor nativo do navegador; a validação em si
   roda no envio do formulário (ver validarDataNascimento), não a cada
   alteração do campo — senão o alerta interrompe o usuário no meio do
   preenchimento (dia/mês/ano são preenchidos em etapas) e zera a data
   inteira antes que ele termine de digitar. */
document.querySelectorAll('input[type="date"]').forEach(input => {
    input.min = "1900-01-01";
    input.max = new Date().toISOString().split("T")[0];
});

function validarDataNascimento(form) {
    const input = form.querySelector('input[type="date"]');
    if (!input) return true;

    const dataSelecionada = new Date(input.value);
    const dataMinima = new Date("1900-01-01");
    const hoje = new Date();

    hoje.setHours(0, 0, 0, 0);

    if (!input.value || isNaN(dataSelecionada) || dataSelecionada < dataMinima || dataSelecionada > hoje) {
        alert("A data de nascimento deve estar entre 01/01/1900 e hoje.");
        input.focus();
        return false;
    }

    return true;
}


/* ==================================================
   ENVIO DOS FORMULÁRIOS (fetch -> API JSON do backend)
================================================== */

function mostrarErro(elementoMensagem, texto) {
    elementoMensagem.textContent = texto;
    elementoMensagem.className = "mensagem mensagem-erro";
}

// Caso especial do form de técnico: o email já é de uma conta cliente. Não
// é duplicidade de verdade, é alguém que quer converter a conta existente —
// isso exige provar dono fazendo login, então aqui só apontamos o caminho
// (em vez do texto genérico de "email já cadastrado").
function mostrarContaExistente(elementoMensagem) {
    elementoMensagem.innerHTML = 'Este email já tem uma conta de cliente. <a href="/">Faça login</a> e converta sua conta em técnico pela área do cliente.';
    elementoMensagem.className = "mensagem mensagem-erro";
}

async function enviarCadastro(form, url, elementoMensagem) {
    // FormData funciona tanto pra campos de texto quanto de arquivo
    // (o form do técnico tem enctype implícito porque usamos fetch:
    // o navegador monta o multipart/form-data sozinho a partir do FormData).
    const formData = new FormData(form);

    // coordenadasPromise (geolocalizacao.js) foi disparada no load da
    // página, então geralmente já está resolvida aqui — não trava o envio.
    anexarCoordenadas(formData, await coordenadasPromise);

    const resposta = await fetch(url, {
        method: "POST",
        body: formData,
    });
    const dados = await resposta.json();

    if (!dados.ok) {
        if (dados.conta_existente === "cliente") {
            mostrarContaExistente(elementoMensagem);
        } else {
            mostrarErro(elementoMensagem, dados.erro);
        }
        return;
    }

    window.location.href = dados.redirect;
}

document.getElementById("clienteForm").addEventListener("submit", (evento) => {
    evento.preventDefault();
    if (!validarDataNascimento(evento.target)) return;
    enviarCadastro(evento.target, "/api/cadastro/cliente", document.getElementById("mensagemCliente"));
});

document.getElementById("tecnicoForm").addEventListener("submit", (evento) => {
    evento.preventDefault();
    if (!validarDataNascimento(evento.target)) return;
    enviarCadastro(evento.target, "/api/cadastro/tecnico", document.getElementById("mensagemTecnico"));
});

avisarSeSemLocalizacao("avisoLocalizacaoCliente");
avisarSeSemLocalizacao("avisoLocalizacaoTecnico");
