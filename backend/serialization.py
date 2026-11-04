"""Serializers explícitos. Nunca percorre colunas ORM nem __dict__."""
from datetime import date, datetime, timezone
from decimal import Decimal
from collections.abc import Mapping
from flask.json.provider import DefaultJSONProvider
from sqlalchemy.engine import Row
from constants import (
    CAUSAS_DEFEITO_LABELS, DIAS_SEMANA_LABELS, GARANTIA_TIPOS_LABELS,
    MODALIDADES_LABELS, URGENCIA_TAXA_PERCENTUAL,
)

def isoformat_utc(value):
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()

LINK_POR_PAPEL = {"cliente": "/cliente/chamados", "tecnico": "/tecnico/home"}

SERIALIZERS = {}

def to_jsonable(value):
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, datetime):
        return isoformat_utc(value)
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("Decimal não finito não é JSON.")
        return float(value)
    if isinstance(value, float):
        import math
        if not math.isfinite(value):
            raise ValueError("Número não finito não é JSON.")
        return value
    if isinstance(value, Row):
        value = value._mapping
    if isinstance(value, Mapping):
        return {key: to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(item) for item in value]
    serializer = SERIALIZERS.get(type(value).__name__)
    if serializer:
        return to_jsonable(serializer(value))
    raise TypeError(f"Sem serializer explícito para {type(value).__name__}")

class IFixJSONProvider(DefaultJSONProvider):
    def dumps(self, obj, **kwargs):
        return super().dumps(to_jsonable(obj), **kwargs)

def serializar_Atendimento(self):
    return {
        "id": self.id,
        "titulo": self.titulo,
        "descricao": self.descricao,
        "status": self.status,
        "valor_orcamento": self.valor_orcamento if self.valor_orcamento is not None else None,
        "prazo_estimado_dias": self.prazo_estimado_dias,
        "cliente_id": self.cliente_id,
        "tecnico_id": self.tecnico_id,
        "servico_id": self.servico_id,
        "criado_em": isoformat_utc(self.criado_em),
        "atualizado_em": isoformat_utc(self.atualizado_em),
    }


def serializar_Avaliacao(self):
    return {
        "id": self.id,
        "servico_id": self.servico_id,
        "autor_id": self.autor_id,
        "autor_nome": self.autor.nome if self.autor else None,
        "avaliado_id": self.avaliado_id,
        "avaliado_nome": self.avaliado.nome if self.avaliado else None,
        "nota": self.nota,
        "nota_tempo": self.nota_tempo,
        "nota_honestidade": self.nota_honestidade,
        "nota_preco_justo": self.nota_preco_justo,
        "nota_comportamento": self.nota_comportamento,
        "nota_colaboracao": self.nota_colaboracao,
        "comentario": self.comentario,
        "criado_em": isoformat_utc(self.criado_em),
    }


def serializar_MensagemChamado(self):
    return {
        "id": self.id,
        "servico_id": self.servico_id,
        "autor_id": self.autor_id,
        "autor_nome": self.autor.nome if self.autor else None,
        "conteudo": self.conteudo,
        "lida_em": isoformat_utc(self.lida_em),
        "criado_em": isoformat_utc(self.criado_em),
    }


def serializar_Notificacao(self):
    return {
        "id": self.id,
        "servico_id": self.servico_id,
        "papel": self.papel,
        "tipo": self.tipo,
        "titulo": self.titulo,
        "mensagem": self.mensagem,
        "link": LINK_POR_PAPEL.get(self.papel),
        "lida": self.lida_em is not None,
        "criado_em": isoformat_utc(self.criado_em),
    }


def serializar_SolicitacaoAprovacao(self):
    return {
        "id": self.id,
        "servico_id": self.servico_id,
        "tecnico_id": self.tecnico_id,
        "tecnico_nome": self.tecnico.nome if self.tecnico else None,
        "descricao": self.descricao,
        "valor_adicional": self.valor_adicional if self.valor_adicional is not None else 0.0,
        "status": self.status,
        "justificativa_recusa": self.justificativa_recusa,
        "criado_em": isoformat_utc(self.criado_em),
        "respondido_em": isoformat_utc(self.respondido_em),
    }


def serializar_AcionamentoGarantia(self):
    return {
        "id": self.id,
        "servico_id": self.servico_id,
        "cliente_id": self.cliente_id,
        "descricao_problema": self.descricao_problema,
        "tipo_solicitado": self.tipo_solicitado,
        "tipo_solicitado_label": GARANTIA_TIPOS_LABELS.get(self.tipo_solicitado),
        "status": self.status,
        "servico_novo_id": self.servico_novo_id,
        "servico_novo_codigo": self.servico_novo.codigo if self.servico_novo else None,
        "criado_em": isoformat_utc(self.criado_em),
        "respondido_em": isoformat_utc(self.respondido_em),
    }


def serializar_HistoricoServico(self):
    return {
        "id": self.id,
        "servico_id": self.servico_id,
        "status_anterior": self.status_anterior,
        "status_novo": self.status_novo,
        "alterado_por_id": self.alterado_por_id,
        "alterado_por_nome": self.alterado_por.nome if self.alterado_por else None,
        "alterado_em": isoformat_utc(self.alterado_em),
    }


def serializar_Servico(self):
    return {
        "id": self.id,
        "codigo": self.codigo,
        "titulo": self.titulo,
        "descricao": self.descricao,
        "categoria": self.categoria,
        "tipo_equipamento": self.tipo_equipamento,
        "equipamento": self.equipamento,
        "preco_estimado": self.preco_estimado if self.preco_estimado is not None else 0.0,
        "valor_maximo_aprovado": self.valor_maximo_aprovado if self.valor_maximo_aprovado is not None else None,
        "gorjeta": self.gorjeta if self.gorjeta is not None else None,
        "raio_busca_km": self.raio_busca_km,
        "garantia": bool(self.garantia),
        "urgente": bool(self.urgente),
        "urgencia_taxa_percentual": URGENCIA_TAXA_PERCENTUAL if self.urgente else None,
        "urgencia_prazo_em": isoformat_utc(self.urgencia_prazo_em),
        "modalidade": self.modalidade,
        "modalidade_label": MODALIDADES_LABELS.get(self.modalidade),
        "garantia_ativa": self.garantia_ativa,
        "garantia_expira_em": isoformat_utc(self.garantia_expira_em),
        "garantia_dias_restantes": self.garantia_dias_restantes,
        "finalizado_em": isoformat_utc(self.finalizado_em),
        "status": self.status,
        "causa_defeito": self.causa_defeito,
        "causa_defeito_label": CAUSAS_DEFEITO_LABELS.get(self.causa_defeito),
        "laudo_tecnico": self.laudo_tecnico,
        "solucao_aplicada": self.solucao_aplicada,
        "latitude": self.latitude,
        "longitude": self.longitude,
        "cliente_id": self.cliente_id,
        "tecnico_id": self.tecnico_id,
        "criado_em": isoformat_utc(self.criado_em),
        "atualizado_em": isoformat_utc(self.atualizado_em),
        "fotos": [foto.to_dict() for foto in self.fotos],
    }


def serializar_FotoServico(self):
    from uploads import photo_url
    url = photo_url(self.id,self.servico_id,self.arquivo)
    return {
        "id": self.id,
        "arquivo": url,
        "url": url,
        "enviado_em": isoformat_utc(self.enviado_em),
    }


def serializar_SolicitacaoTecnico(self):
    return {
        "id": self.id,
        "servico_id": self.servico_id,
        "tecnico_id": self.tecnico_id,
        "status": self.status,
        "criado_em": isoformat_utc(self.criado_em),
        "respondido_em": isoformat_utc(self.respondido_em),
    }


def serializar_JanelaDisponibilidade(self):
    return {
        "dia_semana": self.dia_semana,
        "dia_label": DIAS_SEMANA_LABELS[self.dia_semana],
        "inicio": self.inicio,
        "fim": self.fim,
    }


def serializar_PerfilTecnico(self):
    return {
        "id": self.id,
        "especialidade": self.especialidade,
        "escolaridade": self.escolaridade,
        "curso_superior": self.curso_superior,
        "regiao_atendimento": self.regiao_atendimento,
        "cursos_experiencias": self.cursos_experiencias,
        "especializacoes": self.especializacoes,
        "foto_perfil": self.foto_perfil,
        "valor_medio": self.valor_medio if self.valor_medio is not None else None,
        "nota_media": self.nota_media if self.nota_media is not None else None,
        "total_avaliacoes": self.total_avaliacoes,
        "modalidades": self.modalidades_lista,
        "disponivel_agora": self.disponivel_agora,
        "disponivel_ate": isoformat_utc(self.disponivel_ate) if self.disponivel_agora else None,
    }


def serializar_Diploma(self):
    return {
        "id": self.id,
        "arquivo": self.arquivo,
        "enviado_em": isoformat_utc(self.enviado_em),
    }


def serializar_Usuario(self):
    return {
        "id": self.id,
        "nome": self.nome,
        "email": self.email,
        "telefone": self.telefone,
        "cpf": self.cpf,
        "role": self.role,
        "eh_tecnico": self.eh_tecnico,
        # Fallback pra foto do perfil técnico: quem virou técnico antes
        # desta coluna existir tem a foto só lá, e ela continua valendo.
        "foto_perfil": self.foto_perfil or (
            self.perfil_tecnico.foto_perfil if self.perfil_tecnico else None
        ),
        "data_nascimento": self.data_nascimento.isoformat() if self.data_nascimento else None,
        "cep": self.cep,
        "cidade": self.cidade,
        "estado": self.estado,
        "bairro": self.bairro,
        "endereco": self.endereco,
        "numero": self.numero,
        "complemento": self.complemento,
        "pais": self.pais,
        "latitude": self.latitude,
        "longitude": self.longitude,
        "alertas_comportamento": self.alertas_comportamento,
        "suspenso": self.suspenso,
        "horario_inicio_atendimento": self.horario_inicio_atendimento,
        "horario_fim_atendimento": self.horario_fim_atendimento,
        "criado_em": isoformat_utc(self.criado_em),
    }


SERIALIZERS.update({
    "Atendimento": serializar_Atendimento,
    "Avaliacao": serializar_Avaliacao,
    "MensagemChamado": serializar_MensagemChamado,
    "Notificacao": serializar_Notificacao,
    "SolicitacaoAprovacao": serializar_SolicitacaoAprovacao,
    "AcionamentoGarantia": serializar_AcionamentoGarantia,
    "HistoricoServico": serializar_HistoricoServico,
    "Servico": serializar_Servico,
    "FotoServico": serializar_FotoServico,
    "SolicitacaoTecnico": serializar_SolicitacaoTecnico,
    "JanelaDisponibilidade": serializar_JanelaDisponibilidade,
    "PerfilTecnico": serializar_PerfilTecnico,
    "Diploma": serializar_Diploma,
    "Usuario": serializar_Usuario,
})
