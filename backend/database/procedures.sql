-- Procedures/functions chamadas pelas Repositories (arquitetura da
-- disciplina: Repository só existe pra consulta com JOIN entre tabelas, e
-- só pode acessar o banco por procedure — nunca via Model/SQLAlchemy ORM
-- direto). Aplicado no Postgres (Neon) automaticamente a cada start do app
-- (ver _instalar_procedures em backend/app.py) — CREATE OR REPLACE é
-- idempotente, então rodar de novo em cima de uma versão já instalada não
-- tem efeito colateral.
--
-- As funções que alimentam resposta de API (usadas por *_repository.py e
-- consumidas por jsonify) retornam uma única coluna `dado json` já no
-- formato exato que os Model.to_dict*() equivalentes produziam — assim a
-- Repository só repassa o resultado, sem reconstruir objeto/Model nenhum.


-- Rótulo pt-BR da causa do defeito (funcionalidade 8). Espelha
-- constants.CAUSAS_DEFEITO_LABELS, que é o que Servico.to_dict() usa —
-- as duas listagens abaixo precisam devolver o mesmo texto que o to_dict(),
-- senão a mesma tela mostraria rótulos diferentes dependendo do endpoint.
-- Prazo de garantia em dias (funcionalidade 2). Espelha GARANTIA_DIAS de
-- constants.py — está numa função só pra não ficar um INTERVAL '10 days'
-- solto em cada lugar que calcula validade, que é como esse tipo de regra
-- diverge silenciosamente do backend.
CREATE OR REPLACE FUNCTION fn_garantia_dias()
RETURNS integer AS $$
    SELECT 10;
$$ LANGUAGE sql IMMUTABLE;


-- Momento em que a garantia de um chamado expira, ou NULL se ele não tem
-- garantia contratada ou ainda não foi finalizado.
CREATE OR REPLACE FUNCTION fn_garantia_expira_em(p_garantia boolean, p_finalizado_em timestamp)
RETURNS timestamp AS $$
    SELECT CASE WHEN NOT p_garantia OR p_finalizado_em IS NULL THEN NULL
        ELSE p_finalizado_em + (fn_garantia_dias() || ' days')::interval END;
$$ LANGUAGE sql IMMUTABLE;


CREATE OR REPLACE FUNCTION fn_rotulo_causa_defeito(p_causa varchar)
RETURNS varchar AS $$
    SELECT CASE p_causa
        WHEN 'componente_defeituoso' THEN 'Componente defeituoso'
        WHEN 'superaquecimento'      THEN 'Superaquecimento'
        WHEN 'dano_por_liquido'      THEN 'Dano por líquido'
        WHEN 'software_corrompido'   THEN 'Software corrompido'
        WHEN 'malware'               THEN 'Vírus / malware'
        WHEN 'desgaste_natural'      THEN 'Desgaste natural'
        WHEN 'mau_uso'               THEN 'Mau uso'
        WHEN 'outro'                 THEN 'Outro'
        ELSE NULL
    END;
$$ LANGUAGE sql IMMUTABLE;


-- Taxa da urgência, em % (funcionalidade 1). Espelha URGENCIA_TAXA_PERCENTUAL
-- de constants.py, que é o que Servico.to_dict() usa.
CREATE OR REPLACE FUNCTION fn_urgencia_taxa_percentual()
RETURNS integer AS $$
    SELECT 20;
$$ LANGUAGE sql IMMUTABLE;


-- Rótulo pt-BR da modalidade de atendimento (funcionalidade 2). Espelha
-- constants.MODALIDADES_LABELS, que é o que Servico.to_dict() usa.
CREATE OR REPLACE FUNCTION fn_rotulo_modalidade(p_modalidade varchar)
RETURNS varchar AS $$
    SELECT CASE p_modalidade
        WHEN 'loja'      THEN 'Na loja do técnico'
        WHEN 'domicilio' THEN 'Visita domiciliar'
        WHEN 'remoto'    THEN 'Suporte remoto'
        ELSE NULL
    END;
$$ LANGUAGE sql IMMUTABLE;


-- Modalidades efetivas do técnico como array JSON. Coluna nula/vazia =
-- nunca configurou = atende todas (mesma regra de PerfilTecnico.modalidades_lista).
CREATE OR REPLACE FUNCTION fn_modalidades_json(p_modalidades varchar)
RETURNS json AS $$
    SELECT CASE
        WHEN p_modalidades IS NULL OR p_modalidades = ''
            THEN to_json(ARRAY['loja', 'domicilio', 'remoto'])
        ELSE to_json(string_to_array(p_modalidades, ','))
    END;
$$ LANGUAGE sql IMMUTABLE;


-- "Disponível agora" (funcionalidade 6): o status vale até disponivel_ate,
-- gravado em UTC (mesma régua de garantia_ativa, acima).
CREATE OR REPLACE FUNCTION fn_tecnico_disponivel_agora(p_disponivel_ate timestamp)
RETURNS boolean AS $$
    SELECT COALESCE(p_disponivel_ate > (NOW() AT TIME ZONE 'UTC'), FALSE);
$$ LANGUAGE sql STABLE;


-- Métricas do técnico (funcionalidades 5 e 7), calculadas sobre os chamados
-- em que ele foi o responsável.
CREATE OR REPLACE FUNCTION fn_tecnico_atendimentos_concluidos(p_usuario_id integer)
RETURNS bigint AS $$
    SELECT COUNT(*) FROM servicos s
    WHERE s.tecnico_id = p_usuario_id AND s.status = 'finalizado';
$$ LANGUAGE sql STABLE;


-- Taxa de sucesso em %: finalizados / (finalizados + cancelados). Chamado
-- ainda em andamento não conta pra nenhum dos lados. NULL sem histórico.
CREATE OR REPLACE FUNCTION fn_tecnico_taxa_sucesso(p_usuario_id integer)
RETURNS numeric AS $$
    SELECT CASE WHEN COUNT(*) = 0 THEN NULL
        ELSE ROUND(100.0 * COUNT(*) FILTER (WHERE s.status = 'finalizado') / COUNT(*), 0) END
    FROM servicos s
    WHERE s.tecnico_id = p_usuario_id AND s.status IN ('finalizado', 'cancelado');
$$ LANGUAGE sql STABLE;


-- Tempo médio de atendimento em horas: da escolha do técnico (primeira
-- entrada em 'aguardando' no histórico) até a finalização. NULL sem histórico.
CREATE OR REPLACE FUNCTION fn_tecnico_tempo_medio_horas(p_usuario_id integer)
RETURNS numeric AS $$
    SELECT ROUND(AVG(EXTRACT(EPOCH FROM (s.finalizado_em - h.inicio)) / 3600.0)::numeric, 1)
    FROM servicos s
    JOIN LATERAL (
        SELECT MIN(hs.alterado_em) AS inicio
        FROM historico_servicos hs
        WHERE hs.servico_id = s.id AND hs.status_novo = 'aguardando'
    ) h ON h.inicio IS NOT NULL
    WHERE s.tecnico_id = p_usuario_id
      AND s.status = 'finalizado'
      AND s.finalizado_em IS NOT NULL
      AND s.finalizado_em >= h.inicio;
$$ LANGUAGE sql STABLE;


-- Selo "Especialista verificado" (funcionalidade 7), regra automática.
-- Espelha SELO_MIN_ATENDIMENTOS (5), SELO_NOTA_MINIMA (4.5) e
-- SELO_MIN_CERTIFICADOS (1) de constants.py. Técnico sem perfil devolve NULL.
CREATE OR REPLACE FUNCTION fn_tecnico_eh_especialista(p_usuario_id integer)
RETURNS boolean AS $$
    SELECT fn_tecnico_atendimentos_concluidos(p_usuario_id) >= 5
       AND COALESCE(pt.nota_media, 0) >= 4.5
       AND (SELECT COUNT(*) FROM diplomas d WHERE d.perfil_tecnico_id = pt.id) >= 1
    FROM perfis_tecnicos pt
    WHERE pt.usuario_id = p_usuario_id;
$$ LANGUAGE sql STABLE;


-- UsuarioRepository.buscar_tecnicos_com_perfil()
-- Usada por ListarTecnicosService -> GET /api/usuarios/tecnicos.
CREATE OR REPLACE FUNCTION fn_listar_tecnicos_com_perfil()
RETURNS TABLE(dado json) AS $$
    SELECT json_build_object(
        'id', u.id,
        'nome', u.nome,
        'email', u.email,
        'telefone', u.telefone,
        'cpf', u.cpf,
        'role', u.role,
        'cidade', u.cidade,
        'estado', u.estado,
        'pais', u.pais,
        'latitude', u.latitude,
        'longitude', u.longitude,
        'alertas_comportamento', u.alertas_comportamento,
        'suspenso', u.suspenso,
        'criado_em', to_char(u.criado_em, 'YYYY-MM-DD"T"HH24:MI:SS.US') || '+00:00'
    )
    FROM usuarios u
    JOIN perfis_tecnicos pt ON pt.usuario_id = u.id
    WHERE u.role = 'tecnico';
$$ LANGUAGE sql STABLE;


-- UsuarioRepository.buscar_tecnicos_para_ranking()
-- Usada por SelecionarTecnicosService (ranking Haversine + nota + preço) —
-- retorna colunas cruas (não JSON) porque quem consome é cálculo em
-- Python, não uma resposta de API. modalidades (funcionalidade 2) e
-- disponivel_agora (funcionalidade 6) entram pro filtro e pro desempate.
-- DROP antes: o Postgres não deixa CREATE OR REPLACE mudar as colunas de
-- retorno de uma função que já existe.
DROP FUNCTION IF EXISTS fn_listar_tecnicos_para_ranking();
CREATE OR REPLACE FUNCTION fn_listar_tecnicos_para_ranking()
RETURNS TABLE(
    usuario_id integer,
    latitude double precision,
    longitude double precision,
    valor_medio numeric,
    nota_media numeric,
    modalidades varchar,
    disponivel_agora boolean
) AS $$
    SELECT u.id, u.latitude, u.longitude, pt.valor_medio, pt.nota_media,
           pt.modalidades, fn_tecnico_disponivel_agora(pt.disponivel_ate)
    FROM usuarios u
    JOIN perfis_tecnicos pt ON pt.usuario_id = u.id
    WHERE u.role = 'tecnico'
      AND u.latitude IS NOT NULL
      AND u.longitude IS NOT NULL;
$$ LANGUAGE sql STABLE;


-- AtendimentoRepository.listar_por_servico_com_tecnico(servico_id)
-- Usada por ListarOrcamentosService -> GET /api/servicos/<id>/orcamentos.
-- Formato igual a Atendimento.to_dict_com_tecnico().
CREATE OR REPLACE FUNCTION fn_listar_orcamentos_por_servico(p_servico_id integer)
RETURNS TABLE(dado json) AS $$
    SELECT json_build_object(
        'id', a.id,
        'titulo', a.titulo,
        'descricao', a.descricao,
        'status', a.status,
        'valor_orcamento', a.valor_orcamento,
        'prazo_estimado_dias', a.prazo_estimado_dias,
        'cliente_id', a.cliente_id,
        'tecnico_id', a.tecnico_id,
        'servico_id', a.servico_id,
        'criado_em', to_char(a.criado_em, 'YYYY-MM-DD"T"HH24:MI:SS.US') || '+00:00',
        'atualizado_em', to_char(a.atualizado_em, 'YYYY-MM-DD"T"HH24:MI:SS.US') || '+00:00',
        'tecnico', CASE WHEN t.id IS NULL THEN NULL ELSE json_build_object(
            'id', t.id,
            'nome', t.nome,
            'telefone', t.telefone,
            'foto_perfil', COALESCE(t.foto_perfil, pt.foto_perfil),
            'nota_media', pt.nota_media,
            'total_avaliacoes', COALESCE(pt.total_avaliacoes, 0),
            -- Comparativo de propostas (funcionalidades 7 e 8): o cliente
            -- decide olhando também selo, disponibilidade e histórico.
            'especialista_verificado', COALESCE(fn_tecnico_eh_especialista(t.id), FALSE),
            'disponivel_agora', fn_tecnico_disponivel_agora(pt.disponivel_ate),
            'atendimentos_concluidos', fn_tecnico_atendimentos_concluidos(t.id),
            'taxa_sucesso', fn_tecnico_taxa_sucesso(t.id)
        ) END
    )
    FROM atendimentos a
    LEFT JOIN usuarios t ON t.id = a.tecnico_id
    LEFT JOIN perfis_tecnicos pt ON pt.usuario_id = t.id
    WHERE a.servico_id = p_servico_id
    ORDER BY a.criado_em;
$$ LANGUAGE sql STABLE;


-- AprovacaoRepository.listar_por_servico(servico_id)
-- Usada por ListarAprovacoesService -> GET /api/servicos/<id>/aprovacoes.
-- Formato igual a SolicitacaoAprovacao.to_dict() (funcionalidades 6 e 7).
-- respondido_em é NULL enquanto o cliente não respondeu, e o to_char tem que
-- respeitar isso em vez de virar a string "+00:00" sozinha.
CREATE OR REPLACE FUNCTION fn_listar_aprovacoes_por_servico(p_servico_id integer)
RETURNS TABLE(dado json) AS $$
    SELECT json_build_object(
        'id', ap.id,
        'servico_id', ap.servico_id,
        'tecnico_id', ap.tecnico_id,
        'tecnico_nome', t.nome,
        'descricao', ap.descricao,
        'valor_adicional', COALESCE(ap.valor_adicional, 0),
        'status', ap.status,
        'justificativa_recusa', ap.justificativa_recusa,
        'criado_em', to_char(ap.criado_em, 'YYYY-MM-DD"T"HH24:MI:SS.US') || '+00:00',
        'respondido_em', CASE WHEN ap.respondido_em IS NULL THEN NULL
            ELSE to_char(ap.respondido_em, 'YYYY-MM-DD"T"HH24:MI:SS.US') || '+00:00' END
    )
    FROM solicitacoes_aprovacao ap
    LEFT JOIN usuarios t ON t.id = ap.tecnico_id
    WHERE ap.servico_id = p_servico_id
    ORDER BY ap.criado_em DESC;
$$ LANGUAGE sql STABLE;


-- ServicoRepository.buscar_meus_com_participantes(usuario_id, como, status)
-- Usada por ListarMeusServicosService -> GET /api/servicos/meus.
-- Formato igual a Servico.to_dict_painel() (que já inclui as fotos do
-- to_dict() base).
CREATE OR REPLACE FUNCTION fn_listar_servicos_participante(
    p_usuario_id integer,
    p_como varchar,
    p_status varchar DEFAULT NULL
)
RETURNS TABLE(dado json) AS $$
    SELECT json_build_object(
        'id', s.id,
        'codigo', 'IFX-' || (1000 + s.id),
        'titulo', s.titulo,
        'descricao', s.descricao,
        'categoria', s.categoria,
        'tipo_equipamento', s.tipo_equipamento,
        'equipamento', s.equipamento,
        'preco_estimado', COALESCE(s.preco_estimado, 0),
        'valor_maximo_aprovado', s.valor_maximo_aprovado,
        'gorjeta', s.gorjeta,
        'raio_busca_km', s.raio_busca_km,
        -- Quantos técnicos já foram acionados neste chamado. Zero significa
        -- que ninguém foi notificado (cliente sem coordenada, ou nenhum
        -- técnico geolocalizado por perto) — o painel do cliente usa isso
        -- pra oferecer "Ampliar busca" em vez de deixá-lo esperando.
        'solicitacoes_enviadas', (
            SELECT COUNT(*) FROM solicitacoes_tecnicos st WHERE st.servico_id = s.id
        ),
        'orcamentos_recebidos', (
            SELECT COUNT(*) FROM atendimentos a
            WHERE a.servico_id = s.id AND a.valor_orcamento IS NOT NULL
        ),
        -- Contagem de avaliacoes: o painel usa isso pra saber que a avaliacao
        -- do outro lado chegou. Sem ela, avaliar nao muda nada na linha de
        -- `servicos`, e a tela so mostraria a nota depois de recarregar.
        'avaliacoes_total', (
            SELECT COUNT(*) FROM avaliacoes av WHERE av.servico_id = s.id
        ),
        'mensagens_nao_lidas', (
            SELECT COUNT(*) FROM mensagens_chamado m
            WHERE m.servico_id = s.id AND m.autor_id <> p_usuario_id AND m.lida_em IS NULL
        ),
        'aprovacoes_pendentes', (
            SELECT COUNT(*) FROM solicitacoes_aprovacao ap
            WHERE ap.servico_id = s.id AND ap.status = 'pendente'
        ),
        'garantia', s.garantia,
        -- Urgência (funcionalidade 1) e modalidade (funcionalidade 2): mesmos
        -- campos de Servico.to_dict().
        'urgente', s.urgente,
        'urgencia_taxa_percentual', CASE WHEN s.urgente THEN fn_urgencia_taxa_percentual() ELSE NULL END,
        'urgencia_prazo_em', CASE WHEN s.urgencia_prazo_em IS NULL THEN NULL
            ELSE to_char(s.urgencia_prazo_em, 'YYYY-MM-DD"T"HH24:MI:SS.US') || '+00:00' END,
        'modalidade', s.modalidade,
        'modalidade_label', fn_rotulo_modalidade(s.modalidade),
        -- Garantia (funcionalidade 2): os mesmos cálculos das properties de
        -- Servico, porque o front usa este payload pra decidir se mostra o
        -- botão "Acionar garantia" e quantos dias ainda restam.
        'finalizado_em', CASE WHEN s.finalizado_em IS NULL THEN NULL
            ELSE to_char(s.finalizado_em, 'YYYY-MM-DD"T"HH24:MI:SS.US') || '+00:00' END,
        'garantia_expira_em', CASE
            WHEN fn_garantia_expira_em(s.garantia, s.finalizado_em) IS NULL THEN NULL
            ELSE to_char(fn_garantia_expira_em(s.garantia, s.finalizado_em),
                         'YYYY-MM-DD"T"HH24:MI:SS.US') || '+00:00' END,
        'garantia_ativa', COALESCE(
            fn_garantia_expira_em(s.garantia, s.finalizado_em) >= (NOW() AT TIME ZONE 'UTC'), FALSE),
        'garantia_dias_restantes', CASE
            WHEN fn_garantia_expira_em(s.garantia, s.finalizado_em) IS NULL THEN NULL
            ELSE GREATEST(EXTRACT(DAY FROM fn_garantia_expira_em(s.garantia, s.finalizado_em)
                                       - (NOW() AT TIME ZONE 'UTC'))::int, 0) END,
        'status', s.status,
        'causa_defeito', s.causa_defeito,
        'causa_defeito_label', fn_rotulo_causa_defeito(s.causa_defeito),
        'laudo_tecnico', s.laudo_tecnico,
        'solucao_aplicada', s.solucao_aplicada,
        'latitude', s.latitude,
        'longitude', s.longitude,
        'cliente_id', s.cliente_id,
        'tecnico_id', s.tecnico_id,
        'criado_em', to_char(s.criado_em, 'YYYY-MM-DD"T"HH24:MI:SS.US') || '+00:00',
        'atualizado_em', to_char(s.atualizado_em, 'YYYY-MM-DD"T"HH24:MI:SS.US') || '+00:00',
        'fotos', COALESCE((
            SELECT json_agg(json_build_object(
                'id', f.id,
                'arquivo', f.arquivo,
                'url', f.arquivo,
                'enviado_em', to_char(f.enviado_em, 'YYYY-MM-DD"T"HH24:MI:SS.US') || '+00:00'
            ) ORDER BY f.enviado_em)
            FROM fotos_servicos f WHERE f.servico_id = s.id
        ), '[]'::json),
        'cliente', CASE WHEN c.id IS NULL THEN NULL ELSE json_build_object(
            'id', c.id, 'nome', c.nome, 'telefone', c.telefone,
            'foto_perfil', c.foto_perfil,
            'horario_inicio_atendimento', c.horario_inicio_atendimento,
            'horario_fim_atendimento', c.horario_fim_atendimento
        ) END,
        'tecnico', CASE WHEN t.id IS NULL THEN NULL ELSE json_build_object(
            'id', t.id, 'nome', t.nome, 'telefone', t.telefone,
            'foto_perfil', t.foto_perfil
        ) END
    )
    FROM servicos s
    JOIN usuarios c ON c.id = s.cliente_id
    LEFT JOIN usuarios t ON t.id = s.tecnico_id
    WHERE (
        (p_como = 'tecnico' AND s.tecnico_id = p_usuario_id)
        OR (p_como = 'cliente' AND s.cliente_id = p_usuario_id)
    )
    AND (p_status IS NULL OR s.status = p_status)
    ORDER BY s.criado_em DESC;
$$ LANGUAGE sql STABLE;


-- SolicitacaoRepository.buscar_pendentes_com_detalhes(tecnico_id)
-- Usada por ListarSolicitacoesPendentesService -> GET /api/solicitacoes.
-- Formato igual a SolicitacaoTecnico.to_dict_painel() (servico vem como
-- Servico.to_dict() puro, sem cliente/tecnico aninhado dentro dele).
CREATE OR REPLACE FUNCTION fn_listar_solicitacoes_pendentes(p_tecnico_id integer)
RETURNS TABLE(dado json) AS $$
    SELECT json_build_object(
        'id', st.id,
        'servico_id', st.servico_id,
        'tecnico_id', st.tecnico_id,
        'status', st.status,
        'criado_em', to_char(st.criado_em, 'YYYY-MM-DD"T"HH24:MI:SS.US') || '+00:00',
        'respondido_em', CASE WHEN st.respondido_em IS NULL THEN NULL
            ELSE to_char(st.respondido_em, 'YYYY-MM-DD"T"HH24:MI:SS.US') || '+00:00' END,
        'servico', json_build_object(
            'id', s.id,
            'codigo', 'IFX-' || (1000 + s.id),
            'titulo', s.titulo,
            'descricao', s.descricao,
            'categoria', s.categoria,
            'tipo_equipamento', s.tipo_equipamento,
            'equipamento', s.equipamento,
            'preco_estimado', COALESCE(s.preco_estimado, 0),
            'valor_maximo_aprovado', s.valor_maximo_aprovado,
            'garantia', s.garantia,
            'urgente', s.urgente,
            'urgencia_taxa_percentual', CASE WHEN s.urgente THEN fn_urgencia_taxa_percentual() ELSE NULL END,
            'urgencia_prazo_em', CASE WHEN s.urgencia_prazo_em IS NULL THEN NULL
                ELSE to_char(s.urgencia_prazo_em, 'YYYY-MM-DD"T"HH24:MI:SS.US') || '+00:00' END,
            'modalidade', s.modalidade,
            'modalidade_label', fn_rotulo_modalidade(s.modalidade),
            'status', s.status,
            'latitude', s.latitude,
            'longitude', s.longitude,
            'cliente_id', s.cliente_id,
            'tecnico_id', s.tecnico_id,
            'criado_em', to_char(s.criado_em, 'YYYY-MM-DD"T"HH24:MI:SS.US') || '+00:00',
            'atualizado_em', to_char(s.atualizado_em, 'YYYY-MM-DD"T"HH24:MI:SS.US') || '+00:00',
            'fotos', COALESCE((
                SELECT json_agg(json_build_object(
                    'id', f.id,
                    'arquivo', f.arquivo,
                    'url', f.arquivo,
                    'enviado_em', to_char(f.enviado_em, 'YYYY-MM-DD"T"HH24:MI:SS.US') || '+00:00'
                ) ORDER BY f.enviado_em)
                FROM fotos_servicos f WHERE f.servico_id = s.id
            ), '[]'::json)
        ),
        'cliente', CASE WHEN c.id IS NULL THEN NULL ELSE json_build_object(
            'id', c.id, 'nome', c.nome, 'telefone', c.telefone,
            'foto_perfil', c.foto_perfil
        ) END
    )
    FROM solicitacoes_tecnicos st
    JOIN servicos s ON s.id = st.servico_id
    LEFT JOIN usuarios c ON c.id = s.cliente_id
    WHERE st.tecnico_id = p_tecnico_id
      AND st.status = 'pendente'
    -- Urgentes primeiro (funcionalidade 1): o prazo de 2h é do cliente.
    ORDER BY s.urgente DESC, st.criado_em DESC;
$$ LANGUAGE sql STABLE;


-- MensagemRepository.listar_por_servico(servico_id, desde_id)
-- Usada por ListarMensagensService -> GET /api/servicos/<id>/mensagens.
-- p_desde_id nulo devolve a conversa inteira (abertura do chat); com valor,
-- devolve só o que chegou depois — é como o polling de 7s do front pede
-- apenas o incremento, em vez de rebaixar tudo e reconstruir a lista.
CREATE OR REPLACE FUNCTION fn_listar_mensagens_chamado(
    p_servico_id integer,
    p_desde_id integer DEFAULT NULL
)
RETURNS TABLE(dado json) AS $$
    SELECT json_build_object(
        'id', m.id,
        'servico_id', m.servico_id,
        'autor_id', m.autor_id,
        'autor_nome', u.nome,
        'autor_foto', u.foto_perfil,
        'conteudo', m.conteudo,
        'lida_em', CASE WHEN m.lida_em IS NULL THEN NULL
            ELSE to_char(m.lida_em, 'YYYY-MM-DD"T"HH24:MI:SS.US') || '+00:00' END,
        'criado_em', to_char(m.criado_em, 'YYYY-MM-DD"T"HH24:MI:SS.US') || '+00:00'
    )
    FROM mensagens_chamado m
    JOIN usuarios u ON u.id = m.autor_id
    WHERE m.servico_id = p_servico_id
      AND (p_desde_id IS NULL OR m.id > p_desde_id)
    ORDER BY m.id;
$$ LANGUAGE sql STABLE;


-- MensagemRepository.contar_nao_lidas_por_servico(usuario_id)
-- Usada por ContarMensagensNaoLidasService -> GET /api/mensagens/nao-lidas.
-- Devolve colunas cruas (e não json) porque o consumidor é o badge dos
-- painéis, montado em Python como {servico_id: quantidade}.
CREATE OR REPLACE FUNCTION fn_contar_mensagens_nao_lidas(p_usuario_id integer)
RETURNS TABLE(servico_id integer, nao_lidas bigint) AS $$
    SELECT m.servico_id, COUNT(*) AS nao_lidas
    FROM mensagens_chamado m
    JOIN servicos s ON s.id = m.servico_id
    WHERE m.autor_id <> p_usuario_id
      AND m.lida_em IS NULL
      AND (s.cliente_id = p_usuario_id OR s.tecnico_id = p_usuario_id)
    GROUP BY m.servico_id;
$$ LANGUAGE sql STABLE;


-- AvaliacaoRepository.listar_por_servico(servico_id)
-- Usada por ListarAvaliacoesService -> GET /api/servicos/<id>/avaliacoes.
-- Substitui o acesso direto por ORM que existia neste caminho (e que fazia
-- um lazy load do nome de autor e avaliado por linha).
CREATE OR REPLACE FUNCTION fn_listar_avaliacoes_por_servico(p_servico_id integer)
RETURNS TABLE(dado json) AS $$
    SELECT json_build_object(
        'id', av.id,
        'servico_id', av.servico_id,
        'autor_id', av.autor_id,
        'autor_nome', autor.nome,
        'avaliado_id', av.avaliado_id,
        'avaliado_nome', avaliado.nome,
        'nota', av.nota,
        'nota_tempo', av.nota_tempo,
        'nota_honestidade', av.nota_honestidade,
        'nota_preco_justo', av.nota_preco_justo,
        'nota_comportamento', av.nota_comportamento,
        'nota_colaboracao', av.nota_colaboracao,
        'comentario', av.comentario,
        'criado_em', to_char(av.criado_em, 'YYYY-MM-DD"T"HH24:MI:SS.US') || '+00:00'
    )
    FROM avaliacoes av
    JOIN usuarios autor ON autor.id = av.autor_id
    JOIN usuarios avaliado ON avaliado.id = av.avaliado_id
    WHERE av.servico_id = p_servico_id
    ORDER BY av.criado_em;
$$ LANGUAGE sql STABLE;


-- UsuarioRepository.listar_diretorio_tecnicos(...)
-- Usada por ListarDiretorioTecnicosService -> GET /api/tecnicos/diretorio
-- (funcionalidade 4). Só campos públicos: sem e-mail, telefone, CPF nem
-- coordenadas. Preço, experiência e nota de fora do sistema ficam de fora do
-- diretório de propósito (decisão do grupo); o preço médio aparece só no
-- perfil público.
--   p_busca      nome, especialidade ou especializações (contém, sem caixa)
--   p_categoria  'hardware'/'software': só quem já finalizou chamado da categoria
--   p_modalidade técnico que atende a modalidade (sem configuração = atende todas)
--   p_nota_minima, p_disponivel (apenas quem está "disponível agora")
--   p_ordem      'nota' (padrão) ou 'atendimentos'
CREATE OR REPLACE FUNCTION fn_listar_tecnicos_diretorio(
    p_busca varchar DEFAULT NULL,
    p_categoria varchar DEFAULT NULL,
    p_modalidade varchar DEFAULT NULL,
    p_nota_minima numeric DEFAULT NULL,
    p_disponivel boolean DEFAULT NULL,
    p_ordem varchar DEFAULT 'nota'
)
RETURNS TABLE(dado json) AS $$
    SELECT json_build_object(
        'id', u.id,
        'nome', u.nome,
        'foto_perfil', COALESCE(u.foto_perfil, pt.foto_perfil),
        'especialidade', pt.especialidade,
        'cidade', u.cidade,
        'estado', u.estado,
        'nota_media', pt.nota_media,
        'total_avaliacoes', COALESCE(pt.total_avaliacoes, 0),
        'modalidades', fn_modalidades_json(pt.modalidades),
        'disponivel_agora', fn_tecnico_disponivel_agora(pt.disponivel_ate),
        'especialista_verificado', COALESCE(fn_tecnico_eh_especialista(u.id), FALSE),
        'atendimentos_concluidos', fn_tecnico_atendimentos_concluidos(u.id),
        'taxa_sucesso', fn_tecnico_taxa_sucesso(u.id)
    )
    FROM usuarios u
    JOIN perfis_tecnicos pt ON pt.usuario_id = u.id
    WHERE (
        p_busca IS NULL
        OR u.nome ILIKE '%' || p_busca || '%'
        OR pt.especialidade ILIKE '%' || p_busca || '%'
        OR COALESCE(pt.especializacoes, '') ILIKE '%' || p_busca || '%'
    )
    AND (
        p_categoria IS NULL
        OR EXISTS (
            SELECT 1 FROM servicos s
            WHERE s.tecnico_id = u.id AND s.categoria = p_categoria AND s.status = 'finalizado'
        )
    )
    AND (
        p_modalidade IS NULL
        OR pt.modalidades IS NULL
        OR pt.modalidades = ''
        OR p_modalidade = ANY(string_to_array(pt.modalidades, ','))
    )
    AND (p_nota_minima IS NULL OR COALESCE(pt.nota_media, 0) >= p_nota_minima)
    AND (p_disponivel IS NOT TRUE OR fn_tecnico_disponivel_agora(pt.disponivel_ate))
    ORDER BY
        CASE WHEN p_ordem = 'atendimentos' THEN fn_tecnico_atendimentos_concluidos(u.id) END DESC NULLS LAST,
        pt.nota_media DESC NULLS LAST,
        COALESCE(pt.total_avaliacoes, 0) DESC,
        u.nome;
$$ LANGUAGE sql STABLE;


-- UsuarioRepository.obter_perfil_publico_tecnico(usuario_id)
-- Usada por ObterPerfilPublicoTecnicoService ->
-- GET /api/tecnicos/<id>/perfil-publico (funcionalidade 5). Sem linha quando
-- o usuário não é técnico. Não expõe e-mail, telefone, CPF nem coordenadas;
-- dos avaliadores sai só o primeiro nome. Os certificados são os diplomas
-- que o próprio técnico enviou (a tela de perfil avisa isso a ele).
CREATE OR REPLACE FUNCTION fn_perfil_publico_tecnico(p_usuario_id integer)
RETURNS TABLE(dado json) AS $$
    SELECT json_build_object(
        'id', u.id,
        'nome', u.nome,
        'foto_perfil', COALESCE(u.foto_perfil, pt.foto_perfil),
        'cidade', u.cidade,
        'estado', u.estado,
        'membro_desde', to_char(u.criado_em, 'YYYY-MM-DD"T"HH24:MI:SS.US') || '+00:00',
        'especialidade', pt.especialidade,
        'escolaridade', pt.escolaridade,
        'curso_superior', pt.curso_superior,
        'regiao_atendimento', pt.regiao_atendimento,
        'cursos_experiencias', pt.cursos_experiencias,
        'especializacoes', pt.especializacoes,
        'preco_medio', pt.valor_medio,
        'nota_media', pt.nota_media,
        'total_avaliacoes', COALESCE(pt.total_avaliacoes, 0),
        'nota_tempo_media', (
            SELECT ROUND(AVG(av.nota_tempo)::numeric, 1)
            FROM avaliacoes av
            JOIN servicos sv ON sv.id = av.servico_id AND sv.tecnico_id = av.avaliado_id
            WHERE av.avaliado_id = u.id
        ),
        'nota_honestidade_media', (
            SELECT ROUND(AVG(av.nota_honestidade)::numeric, 1)
            FROM avaliacoes av
            JOIN servicos sv ON sv.id = av.servico_id AND sv.tecnico_id = av.avaliado_id
            WHERE av.avaliado_id = u.id
        ),
        'nota_preco_justo_media', (
            SELECT ROUND(AVG(av.nota_preco_justo)::numeric, 1)
            FROM avaliacoes av
            JOIN servicos sv ON sv.id = av.servico_id AND sv.tecnico_id = av.avaliado_id
            WHERE av.avaliado_id = u.id
        ),
        'modalidades', fn_modalidades_json(pt.modalidades),
        'disponivel_agora', fn_tecnico_disponivel_agora(pt.disponivel_ate),
        'especialista_verificado', COALESCE(fn_tecnico_eh_especialista(u.id), FALSE),
        'atendimentos_concluidos', fn_tecnico_atendimentos_concluidos(u.id),
        'taxa_sucesso', fn_tecnico_taxa_sucesso(u.id),
        'tempo_medio_atendimento_horas', fn_tecnico_tempo_medio_horas(u.id),
        'certificados', COALESCE((
            SELECT json_agg(json_build_object('id', d.id, 'url', d.arquivo) ORDER BY d.enviado_em)
            FROM diplomas d WHERE d.perfil_tecnico_id = pt.id
        ), '[]'::json),
        'janelas', COALESCE((
            SELECT json_agg(json_build_object(
                'dia_semana', j.dia_semana, 'inicio', j.inicio, 'fim', j.fim
            ) ORDER BY j.dia_semana, j.inicio)
            FROM janelas_disponibilidade j WHERE j.tecnico_id = u.id
        ), '[]'::json),
        'ultimas_avaliacoes', COALESCE((
            SELECT json_agg(r.item ORDER BY r.criado_em DESC)
            FROM (
                SELECT av.criado_em, json_build_object(
                    'nota', av.nota,
                    'comentario', av.comentario,
                    'autor', split_part(autor.nome, ' ', 1),
                    'criado_em', to_char(av.criado_em, 'YYYY-MM-DD"T"HH24:MI:SS.US') || '+00:00'
                ) AS item
                FROM avaliacoes av
                JOIN servicos sv ON sv.id = av.servico_id AND sv.tecnico_id = av.avaliado_id
                JOIN usuarios autor ON autor.id = av.autor_id
                WHERE av.avaliado_id = u.id AND COALESCE(av.comentario, '') <> ''
                ORDER BY av.criado_em DESC
                LIMIT 5
            ) r
        ), '[]'::json)
    )
    FROM usuarios u
    JOIN perfis_tecnicos pt ON pt.usuario_id = u.id
    WHERE u.id = p_usuario_id;
$$ LANGUAGE sql STABLE;


-- ServicoRepository.buscar_historico_aparelho(cliente_id, equipamento, excluir_id)
-- Usada por ObterHistoricoAparelhoService -> GET /api/servicos/historico-aparelho
-- (funcionalidade 10). Só chamados do próprio cliente; o modelo é comparado
-- sem diferença de caixa nem de espaços repetidos.
CREATE OR REPLACE FUNCTION fn_historico_aparelho(
    p_cliente_id integer,
    p_equipamento varchar,
    p_excluir_id integer DEFAULT NULL
)
RETURNS TABLE(dado json) AS $$
    SELECT json_build_object(
        'id', s.id,
        'codigo', 'IFX-' || (1000 + s.id),
        'titulo', s.titulo,
        'equipamento', s.equipamento,
        'status', s.status,
        'causa_defeito', s.causa_defeito,
        'causa_defeito_label', fn_rotulo_causa_defeito(s.causa_defeito),
        'tecnico_nome', t.nome,
        'criado_em', to_char(s.criado_em, 'YYYY-MM-DD"T"HH24:MI:SS.US') || '+00:00',
        'finalizado_em', CASE WHEN s.finalizado_em IS NULL THEN NULL
            ELSE to_char(s.finalizado_em, 'YYYY-MM-DD"T"HH24:MI:SS.US') || '+00:00' END
    )
    FROM servicos s
    LEFT JOIN usuarios t ON t.id = s.tecnico_id
    WHERE s.cliente_id = p_cliente_id
      AND lower(regexp_replace(trim(s.equipamento), '\s+', ' ', 'g'))
        = lower(regexp_replace(trim(p_equipamento), '\s+', ' ', 'g'))
      AND (p_excluir_id IS NULL OR s.id <> p_excluir_id)
    ORDER BY s.criado_em DESC
    LIMIT 10;
$$ LANGUAGE sql STABLE;
