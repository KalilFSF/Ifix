from constants import (
    BONUS_DISPONIVEL_AGORA,
    PESO_AVALIACAO,
    PESO_DISTANCIA,
    PESO_PRECO,
    RAIO_SELECAO_TECNICOS_KM,
    RAIO_SELECAO_TECNICOS_KM_MAXIMO,
    TECNICOS_SELECIONADOS_MAX,
    TECNICOS_SELECIONADOS_MIN,
)
from modules.usuarios.repositories.usuario_repository import UsuarioRepository
from utils import haversine_km

NOTA_MAXIMA = 5.0


class SelecionarTecnicosService:
    """Base do fluxo automático de chamado: dado um Servico recém-criado,
    calcula a distância (Haversine) até cada técnico cadastrado, combina
    isso com avaliação média e preço médio num score único, e devolve os
    IDs dos melhores candidatos dentro de um raio configurável — sem IA e
    sem serviço externo de geolocalização, só Python + SQLAlchemy.
    """

    def __init__(self):
        self.usuario_repository = UsuarioRepository()

    def executar(self, servico, raio_inicial_km=None, ignorar_ids=()):
        """`raio_inicial_km` sobrescreve o raio padrão — é como
        AmpliarBuscaTecnicosService reaproveita esta seleção com um alcance
        maior. `ignorar_ids` tira do lote quem já foi solicitado, pra a
        ampliação devolver só gente nova."""
        if servico.latitude is None or servico.longitude is None:
            # Chamado sem localização (cliente ainda não tem lat/long
            # cadastrados) — não há como ranquear por proximidade, então a
            # seleção automática é pulada (o cliente pode solicitar técnicos
            # manualmente depois via POST /solicitar-tecnicos).
            return []

        candidatos = self._calcular_distancias(servico)
        # Modalidade (funcionalidade 2): só entra quem atende a que o cliente
        # pediu. Sem fallback pra "todos" de propósito — mandar um chamado de
        # visita domiciliar pra quem só atende na loja gastaria o tempo dele.
        candidatos = [c for c in candidatos if self._atende_modalidade(c, servico.modalidade)]
        if ignorar_ids:
            candidatos = [c for c in candidatos if c["usuario_id"] not in set(ignorar_ids)]
        if not candidatos:
            return []

        selecionados = self._filtrar_por_raio(candidatos, raio_inicial_km)
        self._calcular_scores(selecionados)
        selecionados.sort(key=lambda candidato: candidato["score"], reverse=True)

        return [candidato["usuario_id"] for candidato in selecionados[:TECNICOS_SELECIONADOS_MAX]]

    def _calcular_distancias(self, servico):
        candidatos = []
        for linha in self.usuario_repository.buscar_tecnicos_para_ranking():
            distancia_km = haversine_km(servico.latitude, servico.longitude, linha["latitude"], linha["longitude"])
            candidatos.append({
                "usuario_id": linha["usuario_id"],
                "valor_medio": linha["valor_medio"],
                "nota_media": linha["nota_media"],
                "modalidades": linha["modalidades"],
                "disponivel_agora": linha["disponivel_agora"],
                "distancia_km": distancia_km,
            })
        return candidatos

    @staticmethod
    def _atende_modalidade(candidato, modalidade):
        """Técnico sem modalidade configurada (nulo/vazio) atende todas."""
        configuradas = candidato["modalidades"]
        if not configuradas:
            return True
        return modalidade in configuradas.split(",")

    def _filtrar_por_raio(self, candidatos, raio_inicial_km=None):
        raio = raio_inicial_km or RAIO_SELECAO_TECNICOS_KM
        dentro_do_raio = [c for c in candidatos if c["distancia_km"] <= raio]

        # Quando o raio veio de uma ampliação explícita do cliente, ele já é
        # a decisão dele — não faz sentido dobrar por cima disso.
        if raio_inicial_km:
            return dentro_do_raio

        while len(dentro_do_raio) < TECNICOS_SELECIONADOS_MIN and raio < RAIO_SELECAO_TECNICOS_KM_MAXIMO:
            raio *= 2
            dentro_do_raio = [c for c in candidatos if c["distancia_km"] <= raio]

        # Mesmo estourando o raio máximo, se houver QUALQUER técnico
        # cadastrado ele deve ser notificado — nunca deixar o chamado sem
        # nenhum candidato.
        return dentro_do_raio or candidatos

    def _calcular_scores(self, candidatos):
        distancias = [c["distancia_km"] for c in candidatos]
        dist_min, dist_max = min(distancias), max(distancias)

        valores = [float(c["valor_medio"]) for c in candidatos if c["valor_medio"] is not None]
        valor_min, valor_max = (min(valores), max(valores)) if valores else (None, None)

        for candidato in candidatos:
            score_distancia = self._normalizar_inverso(candidato["distancia_km"], dist_min, dist_max)

            nota = candidato["nota_media"]
            score_avaliacao = (float(nota) / NOTA_MAXIMA) if nota is not None else 0.5

            valor = candidato["valor_medio"]
            if valor is None or valor_min is None:
                score_preco = 0.5  # sem preço informado: nem penaliza nem favorece
            else:
                score_preco = self._normalizar_inverso(float(valor), valor_min, valor_max)

            candidato["score"] = (
                PESO_DISTANCIA * score_distancia
                + PESO_AVALIACAO * score_avaliacao
                + PESO_PRECO * score_preco
                # "Disponível agora" (funcionalidade 6) desempata, não decide.
                + (BONUS_DISPONIVEL_AGORA if candidato["disponivel_agora"] else 0)
            )

    @staticmethod
    def _normalizar_inverso(valor, minimo, maximo):
        """Normaliza `valor` para 0..1 dentro do lote de candidatos, invertido
        (o menor valor do lote vira 1.0) — usado tanto pra distância quanto
        pra preço, onde "menor é melhor"."""
        if maximo == minimo:
            return 1.0
        return 1 - ((valor - minimo) / (maximo - minimo))
