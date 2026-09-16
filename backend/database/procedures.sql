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
-- Python, não uma resposta de API.
CREATE OR REPLACE FUNCTION fn_listar_tecnicos_para_ranking()
RETURNS TABLE(
    usuario_id integer,
    latitude double precision,
    longitude double precision,
    valor_medio numeric,
    nota_media numeric
) AS $$
    SELECT u.id, u.latitude, u.longitude, pt.valor_medio, pt.nota_media
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
            'nota_media', pt.nota_media,
            'total_avaliacoes', COALESCE(pt.total_avaliacoes, 0)
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
    ORDER BY st.criado_em DESC;
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
