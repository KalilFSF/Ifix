/* Coordenadas do dispositivo via API nativa do navegador (Geolocation) —
   não é geocoding externo, é a própria localização do aparelho, usada só
   pra alimentar o ranking automático de técnicos no backend (Haversine).
   Nunca bloqueia o fluxo: se o usuário negar a permissão, o navegador não
   suportar, ou a resposta demorar demais, resolve com null e o formulário
   segue sem coordenada (cadastro/chamado continuam funcionando normalmente,
   só ficam de fora da seleção automática). */

function obterCoordenadas(timeoutMs = 8000) {
    return new Promise((resolve) => {
        if (!("geolocation" in navigator)) {
            resolve(null);
            return;
        }
        navigator.geolocation.getCurrentPosition(
            (posicao) => resolve({
                latitude: posicao.coords.latitude,
                longitude: posicao.coords.longitude,
            }),
            () => resolve(null),
            { enableHighAccuracy: false, timeout: timeoutMs, maximumAge: 300000 }
        );
    });
}

/* Dispara o pedido de permissão assim que a página carrega (não no submit),
   pra já estar resolvido quando o usuário terminar de preencher o
   formulário e apertar enviar — evita dar a impressão de que o envio travou. */
const coordenadasPromise = obterCoordenadas();

function anexarCoordenadas(formData, coordenadas) {
    if (!coordenadas) return;
    formData.append("latitude", coordenadas.latitude);
    formData.append("longitude", coordenadas.longitude);
}

/* Mostra um aviso discreto (não bloqueia o formulário) quando o navegador
   não conseguiu localizar o usuário — sem isso a pessoa não tem como saber
   que precisa permitir o acesso à localização pra entrar na busca
   automática de técnicos, já que hoje isso falha em silêncio. */
async function avisarSeSemLocalizacao(elementoId) {
    const coordenadas = await coordenadasPromise;
    if (coordenadas) return;

    const el = document.getElementById(elementoId);
    if (!el) return;
    el.textContent = "Não conseguimos acessar sua localização. Permita o acesso pelo navegador para que o sistema encontre técnicos próximos automaticamente — sem isso, o cadastro/chamado segue normal, só fica de fora dessa busca.";
    el.classList.remove("hidden");
}
