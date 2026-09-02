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
        ), '[]'::json),
        'cliente', CASE WHEN c.id IS NULL THEN NULL ELSE json_build_object(
            'id', c.id, 'nome', c.nome, 'telefone', c.telefone
        ) END,
        'tecnico', CASE WHEN t.id IS NULL THEN NULL ELSE json_build_object(
            'id', t.id, 'nome', t.nome, 'telefone', t.telefone
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
            'id', c.id, 'nome', c.nome, 'telefone', c.telefone
        ) END
    )
    FROM solicitacoes_tecnicos st
    JOIN servicos s ON s.id = st.servico_id
    LEFT JOIN usuarios c ON c.id = s.cliente_id
    WHERE st.tecnico_id = p_tecnico_id
      AND st.status = 'pendente'
    ORDER BY st.criado_em DESC;
$$ LANGUAGE sql STABLE;
