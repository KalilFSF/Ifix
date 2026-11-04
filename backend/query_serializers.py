"""Projeções explícitas das procedures, preservando contratos de leitura."""
from datetime import datetime, timedelta, timezone
from access import invited_payload
from constants import GARANTIA_DIAS, MODALIDADES, MODALIDADES_LABELS, CAUSAS_DEFEITO_LABELS, URGENCIA_TAXA_PERCENTUAL

def project(row, fields):
    return {key: row.get(key) for key in fields.split()}

SERVICE_FIELDS = "id titulo descricao categoria tipo_equipamento equipamento preco_estimado valor_maximo_aprovado gorjeta raio_busca_km garantia urgente urgencia_prazo_em modalidade finalizado_em status causa_defeito laudo_tecnico solucao_aplicada latitude longitude cliente_id tecnico_id criado_em atualizado_em"
REQUEST_SERVICE_FIELDS = "id codigo titulo descricao categoria tipo_equipamento equipamento preco_estimado valor_maximo_aprovado garantia urgente urgencia_taxa_percentual urgencia_prazo_em modalidade modalidade_label status latitude longitude cliente_id tecnico_id criado_em atualizado_em fotos"
ATTENDANCE_FIELDS = "id titulo descricao status valor_orcamento prazo_estimado_dias cliente_id tecnico_id servico_id criado_em atualizado_em"
APPROVAL_FIELDS = "id servico_id tecnico_id tecnico_nome descricao valor_adicional status justificativa_recusa criado_em respondido_em"
REVIEW_FIELDS = "id servico_id autor_id autor_nome avaliado_id avaliado_nome nota nota_tempo nota_honestidade nota_preco_justo nota_comportamento nota_colaboracao comentario criado_em"
DIRECTORY_FIELDS = "id nome foto_perfil especialidade cidade estado nota_media total_avaliacoes modalidades disponivel_agora especialista_verificado atendimentos_concluidos taxa_sucesso"
PUBLIC_FIELDS = DIRECTORY_FIELDS + " membro_desde escolaridade curso_superior regiao_atendimento cursos_experiencias especializacoes preco_medio nota_tempo_media nota_honestidade_media nota_preco_justo_media tempo_medio_atendimento_horas"

def photo(row):
    from uploads import photo_url
    result = project(row, "id arquivo enviado_em")
    result["arquivo"] = photo_url(row["id"],row["servico_id"],row["arquivo"])
    result["url"] = result["arquivo"]
    return result

def service(row, photos=(), now=None):
    result = project(row, SERVICE_FIELDS)
    result["codigo"] = f"IFX-{1000 + row['id']}"
    result["preco_estimado"] = row.get("preco_estimado") or 0
    for key in ("garantia", "urgente"):
        result[key] = bool(row.get(key))
    result["urgencia_taxa_percentual"] = URGENCIA_TAXA_PERCENTUAL if result["urgente"] else None
    result["modalidade_label"] = MODALIDADES_LABELS.get(row.get("modalidade"))
    result["causa_defeito_label"] = CAUSAS_DEFEITO_LABELS.get(row.get("causa_defeito"))
    expiry = row.get("finalizado_em")
    if expiry is not None and result["garantia"]:
        expiry = expiry + timedelta(days=GARANTIA_DIAS)
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
    else:
        expiry = None
    now = now or datetime.now(timezone.utc)
    result["garantia_expira_em"] = expiry
    result["garantia_ativa"] = expiry is not None and now <= expiry
    result["garantia_dias_restantes"] = max((expiry-now).days, 0) if expiry else None
    result["fotos"] = [photo(item) for item in photos if item["servico_id"] == row["id"]]
    return result

def participant(row, prefix, hours=False):
    identifier = row.get(prefix + "_id")
    if identifier is None:
        return None
    result = {"id": identifier}
    fields = "nome telefone foto_perfil"
    if hours:
        fields += " horario_inicio_atendimento horario_fim_atendimento"
    result.update({field: row.get(prefix + "_" + field) for field in fields.split()})
    return result

def services(sets):
    photos = sets[1]
    result = []
    for row in sets[0]:
        item = service(row, photos)
        item.update(project(row, "solicitacoes_enviadas orcamentos_recebidos avaliacoes_total mensagens_nao_lidas aprovacoes_pendentes"))
        item["cliente"] = participant(row, "cliente", hours=True)
        item["tecnico"] = participant(row, "tecnico")
        result.append(item)
    return result

def requests(sets):
    result = []
    for row in sets[0]:
        item = project(row, "id servico_id tecnico_id status criado_em respondido_em")
        source = {key.removeprefix("servico_"): value for key,value in row.items() if key.startswith("servico_")}
        # O identificador do chamado vem da FK da solicitação, sem colisão com st.id.
        source["id"] = row["servico_id"]
        item["servico"] = invited_payload(service(source, sets[1]))
        client_source = dict(row, cliente_id=source["cliente_id"])
        item["cliente"] = {"id":source["cliente_id"], "nome":row.get("cliente_nome"), "foto_perfil":row.get("cliente_foto_perfil")}
        result.append(item)
    return result

def budgets(rows):
    result = []
    for row in rows:
        item = project(row, ATTENDANCE_FIELDS)
        if row["tecnico_publico_id"] is None:
            technician = None
        else:
            technician = {"id": row["tecnico_publico_id"]}
            technician.update({key: row.get("tecnico_"+key) for key in "nome telefone foto_perfil nota_media total_avaliacoes".split()})
            technician.update(project(row, "atendimentos_concluidos taxa_sucesso"))
            technician.update({key: bool(row[key]) for key in ("especialista_verificado", "disponivel_agora")})
        item["tecnico"] = technician
        result.append(item)
    return result

def directory(row):
    result = project(row, DIRECTORY_FIELDS)
    result["modalidades"] = row["modalidades"].split(",") if row.get("modalidades") else list(MODALIDADES)
    for key in ("disponivel_agora", "especialista_verificado"):
        result[key] = bool(row[key])
    return result

def public_profile(sets):
    if not sets[0]:
        return None
    result = project(sets[0][0], PUBLIC_FIELDS)
    result.update(directory(sets[0][0]))
    result["certificados"] = [project(row, "id url") for row in sets[1]]
    result["janelas"] = [project(row, "dia_semana inicio fim") for row in sets[2]]
    result["ultimas_avaliacoes"] = [project(row, "nota comentario autor criado_em") for row in sets[3]]
    return result

def device_history(rows):
    result = []
    for row in rows:
        item = project(row,"id titulo equipamento status causa_defeito tecnico_nome criado_em finalizado_em")
        item["codigo"] = f"IFX-{1000 + row['id']}"
        item["causa_defeito_label"] = CAUSAS_DEFEITO_LABELS.get(row["causa_defeito"])
        result.append(item)
    return result
