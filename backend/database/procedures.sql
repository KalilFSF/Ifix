-- MySQL 8.4. Instalação explícita, somente em schema vazio. Não monta JSON.
-- Strings têm collation explícita para não depender do default do banco Aiven.
-- fn_modalidades_json mantém o nome legado, mas retorna CSV para o serializer Python.
DELIMITER $$

-- Duração contratual fixa da garantia em dias; acompanha constants.GARANTIA_DIAS.
CREATE FUNCTION fn_garantia_dias() RETURNS INT
DETERMINISTIC NO SQL
SQL SECURITY INVOKER
RETURN 10$$

-- Calcula a data de expiração apenas quando há garantia e conclusão.
CREATE FUNCTION fn_garantia_expira_em(p_garantia BOOLEAN, p_finalizado_em DATETIME(6)) RETURNS DATETIME(6)
DETERMINISTIC NO SQL
SQL SECURITY INVOKER
RETURN CASE WHEN NOT p_garantia OR p_finalizado_em IS NULL THEN NULL ELSE DATE_ADD(p_finalizado_em, INTERVAL 10 DAY) END$$

-- Traduz o código padronizado da causa para o rótulo mostrado ao usuário.
CREATE FUNCTION fn_rotulo_causa_defeito(p_causa VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_as_ci) RETURNS VARCHAR(80) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_as_ci
DETERMINISTIC NO SQL
SQL SECURITY INVOKER
RETURN CASE p_causa WHEN 'componente_defeituoso' THEN 'Componente defeituoso' WHEN 'superaquecimento' THEN 'Superaquecimento' WHEN 'dano_por_liquido' THEN 'Dano por líquido' WHEN 'software_corrompido' THEN 'Software corrompido' WHEN 'malware' THEN 'Vírus / malware' WHEN 'desgaste_natural' THEN 'Desgaste natural' WHEN 'mau_uso' THEN 'Mau uso' WHEN 'outro' THEN 'Outro' ELSE NULL END$$

-- Percentual informado na modalidade urgente; não processa cobrança.
CREATE FUNCTION fn_urgencia_taxa_percentual() RETURNS INT
DETERMINISTIC NO SQL
SQL SECURITY INVOKER
RETURN 20$$

-- Traduz loja/domicilio/remoto em texto de apresentação.
CREATE FUNCTION fn_rotulo_modalidade(p_modalidade VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_as_ci) RETURNS VARCHAR(80) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_as_ci
DETERMINISTIC NO SQL
SQL SECURITY INVOKER
RETURN CASE p_modalidade WHEN 'loja' THEN 'Na loja do técnico' WHEN 'domicilio' THEN 'Visita domiciliar' WHEN 'remoto' THEN 'Suporte remoto' ELSE NULL END$$

-- Nome legado: retorna CSV e não JSON; o Python converte para lista.
CREATE FUNCTION fn_modalidades_json(p_modalidades VARCHAR(60) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_as_ci) RETURNS VARCHAR(60) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_as_ci
DETERMINISTIC NO SQL
SQL SECURITY INVOKER
RETURN COALESCE(NULLIF(p_modalidades, ''), 'loja,domicilio,remoto')$$

-- Compara o prazo temporário do perfil com o instante UTC no servidor.
CREATE FUNCTION fn_tecnico_disponivel_agora(p_disponivel_ate DATETIME(6)) RETURNS BOOLEAN
NOT DETERMINISTIC READS SQL DATA
SQL SECURITY INVOKER
RETURN COALESCE(p_disponivel_ate > UTC_TIMESTAMP(6), FALSE)$$

-- Conta os chamados finalizados atribuídos ao técnico.
CREATE FUNCTION fn_tecnico_atendimentos_concluidos(p_usuario_id INT) RETURNS BIGINT
NOT DETERMINISTIC READS SQL DATA
SQL SECURITY INVOKER
BEGIN
 DECLARE total BIGINT;
 SELECT COUNT(*) INTO total FROM servicos WHERE tecnico_id=p_usuario_id AND status='finalizado';
 RETURN total;
END$$

-- Percentual de finalizados entre finalizados/cancelados do técnico.
CREATE FUNCTION fn_tecnico_taxa_sucesso(p_usuario_id INT) RETURNS DECIMAL(5,0)
NOT DETERMINISTIC READS SQL DATA
SQL SECURITY INVOKER
BEGIN
 DECLARE taxa DECIMAL(5,0);
 SELECT ROUND(100.0 * SUM(CASE WHEN status='finalizado' THEN 1 ELSE 0 END) / NULLIF(COUNT(*),0),0) INTO taxa FROM servicos WHERE tecnico_id=p_usuario_id AND status IN ('finalizado','cancelado');
 RETURN taxa;
END$$

-- Média entre início registrado em histórico e conclusão dos chamados.
CREATE FUNCTION fn_tecnico_tempo_medio_horas(p_usuario_id INT) RETURNS DECIMAL(14,1)
NOT DETERMINISTIC READS SQL DATA
SQL SECURITY INVOKER
BEGIN
 DECLARE media DECIMAL(14,1);
 SELECT ROUND(AVG(TIMESTAMPDIFF(MICROSECOND,h.inicio,s.finalizado_em)/3600000000.0),1) INTO media
 FROM servicos s JOIN (SELECT servico_id, MIN(alterado_em) inicio FROM historico_servicos WHERE status_novo='aguardando' GROUP BY servico_id) h ON h.servico_id=s.id
 WHERE s.tecnico_id=p_usuario_id AND s.status='finalizado' AND s.finalizado_em>=h.inicio;
 RETURN media;
END$$

-- Combina quantidade de concluídos, nota mínima e presença de certificado.
CREATE FUNCTION fn_tecnico_eh_especialista(p_usuario_id INT) RETURNS BOOLEAN
NOT DETERMINISTIC READS SQL DATA
SQL SECURITY INVOKER
BEGIN
 DECLARE selo BOOLEAN DEFAULT NULL;
 SELECT fn_tecnico_atendimentos_concluidos(p_usuario_id)>=5 AND COALESCE(pt.nota_media,0)>=4.5 AND (SELECT COUNT(*) FROM diplomas d WHERE d.perfil_tecnico_id=pt.id)>=1 INTO selo FROM perfis_tecnicos pt WHERE pt.usuario_id=p_usuario_id;
 RETURN selo;
END$$

-- Listagem legada sem uso no endpoint atual; fonte local com projeção pública.
CREATE PROCEDURE fn_listar_tecnicos_com_perfil()
READS SQL DATA SQL SECURITY INVOKER
BEGIN
 SELECT u.id,u.nome,u.cidade,u.estado,COALESCE(u.foto_perfil,pt.foto_perfil) foto_perfil,pt.especialidade,pt.nota_media,COALESCE(pt.total_avaliacoes,0) total_avaliacoes,fn_modalidades_json(pt.modalidades) modalidades
 FROM usuarios u JOIN perfis_tecnicos pt ON pt.usuario_id=u.id WHERE u.role='tecnico';
END$$

-- Dados internos de localização/preço/nota para cálculo do ranking em Python.
CREATE PROCEDURE fn_listar_tecnicos_para_ranking()
READS SQL DATA SQL SECURITY INVOKER
BEGIN
 SELECT u.id usuario_id,u.latitude,u.longitude,pt.valor_medio,pt.nota_media,pt.modalidades,fn_tecnico_disponivel_agora(pt.disponivel_ate) disponivel_agora
 FROM usuarios u JOIN perfis_tecnicos pt ON pt.usuario_id=u.id WHERE u.role='tecnico' AND u.latitude IS NOT NULL AND u.longitude IS NOT NULL;
END$$

-- Propostas e dados do técnico para comparação autorizada pelo proprietário.
CREATE PROCEDURE fn_listar_orcamentos_por_servico(IN p_servico_id INT)
READS SQL DATA SQL SECURITY INVOKER
BEGIN
 SELECT a.*,u.id tecnico_publico_id,u.nome tecnico_nome,u.telefone tecnico_telefone,COALESCE(u.foto_perfil,pt.foto_perfil) tecnico_foto_perfil,pt.nota_media tecnico_nota_media,COALESCE(pt.total_avaliacoes,0) tecnico_total_avaliacoes,fn_tecnico_disponivel_agora(pt.disponivel_ate) disponivel_agora,fn_tecnico_atendimentos_concluidos(u.id) atendimentos_concluidos, fn_tecnico_taxa_sucesso(u.id) taxa_sucesso, COALESCE(fn_tecnico_eh_especialista(u.id),FALSE) especialista_verificado
 FROM atendimentos a LEFT JOIN usuarios u ON u.id=a.tecnico_id LEFT JOIN perfis_tecnicos pt ON pt.usuario_id=u.id WHERE a.servico_id=p_servico_id ORDER BY a.criado_em;
END$$

-- Pedidos de custo adicional com identificação do profissional solicitante.
CREATE PROCEDURE fn_listar_aprovacoes_por_servico(IN p_servico_id INT)
READS SQL DATA SQL SECURITY INVOKER
BEGIN
 SELECT ap.*,u.nome tecnico_nome FROM solicitacoes_aprovacao ap LEFT JOIN usuarios u ON u.id=ap.tecnico_id WHERE ap.servico_id=p_servico_id ORDER BY ap.criado_em DESC;
END$$

-- Chamados filtrados pelo participante; segundo conjunto contém fotos desses chamados.
CREATE PROCEDURE fn_listar_servicos_participante(IN p_usuario_id INT, IN p_como VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_as_ci, IN p_status VARCHAR(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_as_ci)
READS SQL DATA SQL SECURITY INVOKER
BEGIN
 SELECT s.*,c.nome cliente_nome,c.telefone cliente_telefone,c.foto_perfil cliente_foto_perfil,c.horario_inicio_atendimento cliente_horario_inicio_atendimento,c.horario_fim_atendimento cliente_horario_fim_atendimento,t.nome tecnico_nome,t.telefone tecnico_telefone,t.foto_perfil tecnico_foto_perfil,
 (SELECT COUNT(*) FROM solicitacoes_tecnicos st WHERE st.servico_id=s.id) solicitacoes_enviadas,
 (SELECT COUNT(*) FROM atendimentos a WHERE a.servico_id=s.id AND a.valor_orcamento IS NOT NULL) orcamentos_recebidos,
 (SELECT COUNT(*) FROM avaliacoes av WHERE av.servico_id=s.id) avaliacoes_total,
 (SELECT COUNT(*) FROM mensagens_chamado m WHERE m.servico_id=s.id AND m.autor_id<>p_usuario_id AND m.lida_em IS NULL) mensagens_nao_lidas,
 (SELECT COUNT(*) FROM solicitacoes_aprovacao ap WHERE ap.servico_id=s.id AND ap.status='pendente') aprovacoes_pendentes
 FROM servicos s JOIN usuarios c ON c.id=s.cliente_id LEFT JOIN usuarios t ON t.id=s.tecnico_id WHERE ((p_como='tecnico' AND s.tecnico_id=p_usuario_id) OR (p_como='cliente' AND s.cliente_id=p_usuario_id)) AND (p_status IS NULL OR s.status=p_status) ORDER BY s.criado_em DESC;
 SELECT f.* FROM fotos_servicos f JOIN servicos s ON s.id=f.servico_id WHERE ((p_como='tecnico' AND s.tecnico_id=p_usuario_id) OR (p_como='cliente' AND s.cliente_id=p_usuario_id)) AND (p_status IS NULL OR s.status=p_status) ORDER BY f.enviado_em;

END$$

-- Convites pendentes do técnico; segundo conjunto contém fotos para preparar orçamento.
CREATE PROCEDURE fn_listar_solicitacoes_pendentes(IN p_tecnico_id INT)
READS SQL DATA SQL SECURITY INVOKER
BEGIN
 SELECT st.*,s.titulo servico_titulo,s.descricao servico_descricao,s.categoria servico_categoria,s.tipo_equipamento servico_tipo_equipamento,s.equipamento servico_equipamento,s.preco_estimado servico_preco_estimado,s.valor_maximo_aprovado servico_valor_maximo_aprovado,s.garantia servico_garantia,s.urgente servico_urgente,s.urgencia_prazo_em servico_urgencia_prazo_em,s.modalidade servico_modalidade,s.status servico_status,s.latitude servico_latitude,s.longitude servico_longitude,s.cliente_id servico_cliente_id,s.tecnico_id servico_tecnico_id,s.criado_em servico_criado_em,s.atualizado_em servico_atualizado_em,u.nome cliente_nome,u.telefone cliente_telefone,u.foto_perfil cliente_foto_perfil
 FROM solicitacoes_tecnicos st JOIN servicos s ON s.id=st.servico_id LEFT JOIN usuarios u ON u.id=s.cliente_id WHERE st.tecnico_id=p_tecnico_id AND st.status='pendente' ORDER BY s.urgente DESC,st.criado_em DESC;
 SELECT DISTINCT f.* FROM fotos_servicos f JOIN solicitacoes_tecnicos st ON st.servico_id=f.servico_id WHERE st.tecnico_id=p_tecnico_id AND st.status='pendente' ORDER BY f.enviado_em;

END$$

-- Mensagens ordenadas por id; desde_id permite sincronização incremental.
CREATE PROCEDURE fn_listar_mensagens_chamado(IN p_servico_id INT, IN p_desde_id INT)
READS SQL DATA SQL SECURITY INVOKER
BEGIN
 SELECT m.*,u.nome autor_nome,u.foto_perfil autor_foto FROM mensagens_chamado m JOIN usuarios u ON u.id=m.autor_id WHERE m.servico_id=p_servico_id AND (p_desde_id IS NULL OR m.id>p_desde_id) ORDER BY m.id;
END$$

-- Contadores por chamado para o usuário, excluindo mensagens próprias já lidas.
CREATE PROCEDURE fn_contar_mensagens_nao_lidas(IN p_usuario_id INT)
READS SQL DATA SQL SECURITY INVOKER
BEGIN
 SELECT m.servico_id,COUNT(*) nao_lidas FROM mensagens_chamado m JOIN servicos s ON s.id=m.servico_id WHERE m.autor_id<>p_usuario_id AND m.lida_em IS NULL AND (s.cliente_id=p_usuario_id OR s.tecnico_id=p_usuario_id) GROUP BY m.servico_id;
END$$

-- Avaliações do chamado com nomes do autor e do avaliado.
CREATE PROCEDURE fn_listar_avaliacoes_por_servico(IN p_servico_id INT)
READS SQL DATA SQL SECURITY INVOKER
BEGIN
 SELECT av.*,autor.nome autor_nome,avaliado.nome avaliado_nome FROM avaliacoes av JOIN usuarios autor ON autor.id=av.autor_id JOIN usuarios avaliado ON avaliado.id=av.avaliado_id WHERE av.servico_id=p_servico_id ORDER BY av.criado_em;
END$$

-- Projeção pública com busca, categoria, modalidade, nota, disponibilidade e ordenação.
CREATE PROCEDURE fn_listar_tecnicos_diretorio(IN p_busca VARCHAR(60) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_as_ci, IN p_categoria VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_as_ci, IN p_modalidade VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_as_ci, IN p_nota_minima DECIMAL(3,2), IN p_disponivel BOOLEAN, IN p_ordem VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_as_ci)
READS SQL DATA SQL SECURITY INVOKER
BEGIN
 SELECT u.id,u.nome,COALESCE(u.foto_perfil,pt.foto_perfil) foto_perfil,pt.especialidade,u.cidade,u.estado,pt.nota_media,COALESCE(pt.total_avaliacoes,0) total_avaliacoes,fn_modalidades_json(pt.modalidades) modalidades,fn_tecnico_disponivel_agora(pt.disponivel_ate) disponivel_agora,fn_tecnico_atendimentos_concluidos(u.id) atendimentos_concluidos, fn_tecnico_taxa_sucesso(u.id) taxa_sucesso, COALESCE(fn_tecnico_eh_especialista(u.id),FALSE) especialista_verificado FROM usuarios u JOIN perfis_tecnicos pt ON pt.usuario_id=u.id
 WHERE (p_busca IS NULL OR u.nome LIKE CONCAT('%',p_busca,'%') OR pt.especialidade LIKE CONCAT('%',p_busca,'%') OR COALESCE(pt.especializacoes,'') LIKE CONCAT('%',p_busca,'%'))
 AND (p_categoria IS NULL OR EXISTS(SELECT 1 FROM servicos s WHERE s.tecnico_id=u.id AND s.categoria=p_categoria AND s.status='finalizado'))
 AND (p_modalidade IS NULL OR pt.modalidades IS NULL OR pt.modalidades='' OR FIND_IN_SET(p_modalidade,pt.modalidades)>0)
 AND (p_nota_minima IS NULL OR COALESCE(pt.nota_media,0)>=p_nota_minima)
 AND (COALESCE(p_disponivel,FALSE)=FALSE OR fn_tecnico_disponivel_agora(pt.disponivel_ate))
 ORDER BY CASE WHEN p_ordem='atendimentos' THEN fn_tecnico_atendimentos_concluidos(u.id) END DESC,pt.nota_media DESC,COALESCE(pt.total_avaliacoes,0) DESC,u.nome;

END$$

-- Quatro conjuntos: perfil/métricas, certificados, janelas e comentários recentes.
CREATE PROCEDURE fn_perfil_publico_tecnico(IN p_usuario_id INT)
READS SQL DATA SQL SECURITY INVOKER
BEGIN
 SELECT u.id,u.nome,COALESCE(u.foto_perfil,pt.foto_perfil) foto_perfil,pt.especialidade,u.cidade,u.estado,pt.nota_media,COALESCE(pt.total_avaliacoes,0) total_avaliacoes,fn_modalidades_json(pt.modalidades) modalidades,fn_tecnico_disponivel_agora(pt.disponivel_ate) disponivel_agora,fn_tecnico_atendimentos_concluidos(u.id) atendimentos_concluidos, fn_tecnico_taxa_sucesso(u.id) taxa_sucesso, COALESCE(fn_tecnico_eh_especialista(u.id),FALSE) especialista_verificado,u.criado_em membro_desde,pt.escolaridade,pt.curso_superior,pt.regiao_atendimento,pt.cursos_experiencias,pt.especializacoes,pt.valor_medio preco_medio,(SELECT ROUND(AVG(av.nota_tempo),1) FROM avaliacoes av JOIN servicos sv ON sv.id=av.servico_id AND sv.tecnico_id=av.avaliado_id WHERE av.avaliado_id=u.id) nota_tempo_media,(SELECT ROUND(AVG(av.nota_honestidade),1) FROM avaliacoes av JOIN servicos sv ON sv.id=av.servico_id AND sv.tecnico_id=av.avaliado_id WHERE av.avaliado_id=u.id) nota_honestidade_media,(SELECT ROUND(AVG(av.nota_preco_justo),1) FROM avaliacoes av JOIN servicos sv ON sv.id=av.servico_id AND sv.tecnico_id=av.avaliado_id WHERE av.avaliado_id=u.id) nota_preco_justo_media,fn_tecnico_tempo_medio_horas(u.id) tempo_medio_atendimento_horas
 FROM usuarios u JOIN perfis_tecnicos pt ON pt.usuario_id=u.id WHERE u.id=p_usuario_id;
 SELECT d.id,d.arquivo url FROM diplomas d JOIN perfis_tecnicos pt ON pt.id=d.perfil_tecnico_id WHERE pt.usuario_id=p_usuario_id ORDER BY d.enviado_em;
 SELECT dia_semana,inicio,fim FROM janelas_disponibilidade WHERE tecnico_id=p_usuario_id ORDER BY dia_semana,inicio;
 SELECT av.nota,av.comentario,SUBSTRING_INDEX(autor.nome,' ',1) autor,av.criado_em FROM avaliacoes av JOIN servicos sv ON sv.id=av.servico_id AND sv.tecnico_id=av.avaliado_id JOIN usuarios autor ON autor.id=av.autor_id WHERE av.avaliado_id=p_usuario_id AND COALESCE(av.comentario,'')<>'' ORDER BY av.criado_em DESC LIMIT 5;

END$$

-- Histórico do cliente por modelo normalizado; exclui id opcional e limita resultados.
CREATE PROCEDURE fn_historico_aparelho(IN p_cliente_id INT, IN p_equipamento VARCHAR(150) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_as_ci, IN p_excluir_id INT)
READS SQL DATA SQL SECURITY INVOKER
BEGIN
 SELECT s.id,s.titulo,s.equipamento,s.status,s.causa_defeito,t.nome tecnico_nome,s.criado_em,s.finalizado_em
 FROM servicos s LEFT JOIN usuarios t ON t.id=s.tecnico_id
 WHERE s.cliente_id=p_cliente_id AND LOWER(REGEXP_REPLACE(TRIM(s.equipamento),'[[:space:]]+',' '))=LOWER(REGEXP_REPLACE(TRIM(p_equipamento),'[[:space:]]+',' ')) AND (p_excluir_id IS NULL OR s.id<>p_excluir_id) ORDER BY s.criado_em DESC LIMIT 10;

END$$

DELIMITER ;
