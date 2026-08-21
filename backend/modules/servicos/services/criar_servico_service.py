from flask import current_app

from constants import (
    CATEGORIAS_PROBLEMA,
    GARANTIA_PERCENTUAL,
    MAX_BYTES_FOTO_CHAMADO,
    MAX_FOTOS_CHAMADO,
    STATUS_ABERTO,
    TIPOS_EQUIPAMENTO,
)
from exceptions import ValidacaoError
from modules.servicos.models.historico import HistoricoServico
from modules.servicos.models.servico import FotoServico, Servico
from utils import IMAGE_EXTENSIONS, extensao_permitida, salvar_arquivo


class CriarServicoService:
    def executar(self, dados, cliente_id, fotos=None):
        dados_limpos = self._validar_dados(dados)
        arquivos = self._validar_fotos(fotos or [])

        servico = Servico.criar(dados_limpos, cliente_id)
        HistoricoServico.registrar(
            servico.id,
            status_anterior=None,
            status_novo=STATUS_ABERTO,
            alterado_por_id=cliente_id,
        )

        if arquivos:
            pasta = current_app.config["UPLOAD_FOLDER"] + "/chamados"
            for arquivo in arquivos:
                nome = salvar_arquivo(arquivo, pasta)
                FotoServico.criar(servico.id, nome)

        return Servico.buscar_por_id(servico.id)

    def _validar_dados(self, dados):
        tipo = (dados.get("tipo_equipamento") or "").strip().lower()
        categoria = (dados.get("categoria") or "").strip().lower()
        equipamento = (dados.get("equipamento") or "").strip()
        titulo = (dados.get("titulo") or "").strip()
        descricao = (dados.get("descricao") or "").strip()
        garantia = self._parse_bool(dados.get("garantia"))

        if tipo not in TIPOS_EQUIPAMENTO:
            raise ValidacaoError("Selecione o tipo de computador (notebook ou desktop).")
        if categoria not in CATEGORIAS_PROBLEMA:
            raise ValidacaoError("Selecione a categoria do problema (hardware ou software).")
        if not equipamento or len(equipamento) < 2:
            raise ValidacaoError("Informe o modelo do equipamento.")
        if not titulo or len(titulo) < 3:
            raise ValidacaoError("Informe um título curto para o problema.")
        if not descricao or len(descricao) < 10:
            raise ValidacaoError("Descreva o problema com mais detalhes.")

        preco = dados.get("preco_estimado", 0)
        try:
            preco = float(preco or 0)
        except (TypeError, ValueError):
            preco = 0
        if preco < 0:
            raise ValidacaoError("O valor estimado não pode ser negativo.")

        # Se já houver valor e a garantia estiver marcada, aplica +7%.
        if garantia and preco > 0:
            preco = round(preco * (1 + GARANTIA_PERCENTUAL), 2)

        return {
            "tipo_equipamento": tipo,
            "categoria": categoria,
            "equipamento": equipamento,
            "titulo": titulo,
            "descricao": descricao,
            "preco_estimado": preco,
            "garantia": garantia,
        }

    @staticmethod
    def _parse_bool(valor):
        if isinstance(valor, bool):
            return valor
        if valor is None:
            return False
        return str(valor).strip().lower() in {"1", "true", "on", "yes", "sim"}

    def _validar_fotos(self, fotos):
        if len(fotos) > MAX_FOTOS_CHAMADO:
            raise ValidacaoError(f"Envie no máximo {MAX_FOTOS_CHAMADO} fotos.")

        validadas = []
        for arquivo in fotos:
            if not arquivo or not arquivo.filename:
                continue
            if not extensao_permitida(arquivo.filename, IMAGE_EXTENSIONS):
                raise ValidacaoError("As fotos devem ser png, jpg, jpeg ou webp.")
            pos = arquivo.stream.tell()
            arquivo.stream.seek(0, 2)
            tamanho = arquivo.stream.tell()
            arquivo.stream.seek(pos)
            if tamanho > MAX_BYTES_FOTO_CHAMADO:
                raise ValidacaoError("Cada foto deve ter no máximo 2 MB.")
            validadas.append(arquivo)
        return validadas
