-- Gerado dos 14 modelos por scripts/gerar_schema.py. Sem dados, DROP ou IF NOT EXISTS.

-- Execute somente no schema vazio explicitamente selecionado pelo inicializador.

SET NAMES utf8mb4 COLLATE utf8mb4_0900_as_ci;

SET time_zone = '+00:00';

CREATE TABLE usuarios (
	id INTEGER NOT NULL AUTO_INCREMENT,
	nome VARCHAR(100) NOT NULL,
	email VARCHAR(120) NOT NULL,
	telefone VARCHAR(20) NOT NULL,
	cpf VARCHAR(11) NOT NULL,
	data_nascimento DATE NOT NULL,
	senha_hash VARCHAR(255) NOT NULL,
	`role` VARCHAR(20) NOT NULL,
	foto_perfil VARCHAR(255),
	pais VARCHAR(50) NOT NULL DEFAULT 'Brasil',
	cep VARCHAR(9),
	estado VARCHAR(2),
	cidade VARCHAR(100),
	bairro VARCHAR(100),
	endereco VARCHAR(150),
	numero VARCHAR(10),
	complemento VARCHAR(150),
	latitude DOUBLE,
	longitude DOUBLE,
	alertas_comportamento INTEGER NOT NULL DEFAULT 0,
	suspenso BOOL NOT NULL DEFAULT 0,
	horario_inicio_atendimento VARCHAR(5) NOT NULL DEFAULT '08:00',
	horario_fim_atendimento VARCHAR(5) NOT NULL DEFAULT '18:00',
	criado_em DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6),
	PRIMARY KEY (id)
)ENGINE=InnoDB CHARSET=utf8mb4 COLLATE utf8mb4_0900_as_ci;

CREATE UNIQUE INDEX ix_usuarios_cpf ON usuarios (cpf);

CREATE UNIQUE INDEX ix_usuarios_email ON usuarios (email);

CREATE TABLE janelas_disponibilidade (
	id INTEGER NOT NULL AUTO_INCREMENT,
	tecnico_id INTEGER NOT NULL,
	dia_semana INTEGER NOT NULL,
	inicio VARCHAR(5) NOT NULL,
	fim VARCHAR(5) NOT NULL,
	FOREIGN KEY(tecnico_id) REFERENCES usuarios (id) ON DELETE CASCADE,
	PRIMARY KEY (id)
)ENGINE=InnoDB CHARSET=utf8mb4 COLLATE utf8mb4_0900_as_ci;

CREATE INDEX ix_janelas_disponibilidade_tecnico_id ON janelas_disponibilidade (tecnico_id);

CREATE TABLE perfis_tecnicos (
	id INTEGER NOT NULL AUTO_INCREMENT,
	usuario_id INTEGER NOT NULL,
	especialidade VARCHAR(100) NOT NULL,
	escolaridade VARCHAR(50) NOT NULL,
	curso_superior VARCHAR(100),
	regiao_atendimento VARCHAR(150) NOT NULL,
	cursos_experiencias TEXT,
	especializacoes TEXT,
	foto_perfil VARCHAR(255) NOT NULL,
	valor_medio NUMERIC(10, 2),
	nota_media NUMERIC(3, 2),
	total_avaliacoes INTEGER NOT NULL DEFAULT 0,
	modalidades VARCHAR(60),
	disponivel_ate DATETIME(6),
	FOREIGN KEY(usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE,
	PRIMARY KEY (id),
	UNIQUE (usuario_id)
)ENGINE=InnoDB CHARSET=utf8mb4 COLLATE utf8mb4_0900_as_ci;

CREATE TABLE servicos (
	id INTEGER NOT NULL AUTO_INCREMENT,
	titulo VARCHAR(150) NOT NULL,
	descricao TEXT NOT NULL,
	categoria VARCHAR(50) NOT NULL,
	tipo_equipamento VARCHAR(20) NOT NULL DEFAULT 'notebook',
	equipamento VARCHAR(150),
	preco_estimado NUMERIC(10, 2) NOT NULL DEFAULT 0,
	valor_maximo_aprovado NUMERIC(10, 2),
	gorjeta NUMERIC(10, 2),
	garantia BOOL NOT NULL DEFAULT 0,
	status VARCHAR(30) NOT NULL DEFAULT 'aberto',
	urgente BOOL NOT NULL DEFAULT 0,
	urgencia_prazo_em DATETIME(6),
	modalidade VARCHAR(20) NOT NULL DEFAULT 'loja',
	raio_busca_km INTEGER,
	causa_defeito VARCHAR(50),
	laudo_tecnico TEXT,
	solucao_aplicada TEXT,
	finalizado_em DATETIME(6),
	latitude DOUBLE,
	longitude DOUBLE,
	cliente_id INTEGER NOT NULL,
	tecnico_id INTEGER,
	criado_em DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6),
	atualizado_em DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6),
	FOREIGN KEY(cliente_id) REFERENCES usuarios (id) ON DELETE CASCADE,
	FOREIGN KEY(tecnico_id) REFERENCES usuarios (id) ON DELETE CASCADE,
	PRIMARY KEY (id)
)ENGINE=InnoDB CHARSET=utf8mb4 COLLATE utf8mb4_0900_as_ci;

CREATE TABLE acionamentos_garantia (
	id INTEGER NOT NULL AUTO_INCREMENT,
	servico_id INTEGER NOT NULL,
	cliente_id INTEGER NOT NULL,
	descricao_problema TEXT NOT NULL,
	tipo_solicitado VARCHAR(20) NOT NULL,
	status VARCHAR(20) NOT NULL DEFAULT 'pendente',
	servico_novo_id INTEGER,
	criado_em DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6),
	respondido_em DATETIME(6),
	FOREIGN KEY(cliente_id) REFERENCES usuarios (id) ON DELETE CASCADE,
	FOREIGN KEY(servico_id) REFERENCES servicos (id) ON DELETE CASCADE,
	FOREIGN KEY(servico_novo_id) REFERENCES servicos (id) ON DELETE SET NULL,
	PRIMARY KEY (id)
)ENGINE=InnoDB CHARSET=utf8mb4 COLLATE utf8mb4_0900_as_ci;

CREATE TABLE atendimentos (
	id INTEGER NOT NULL AUTO_INCREMENT,
	titulo VARCHAR(150) NOT NULL,
	descricao TEXT NOT NULL,
	status VARCHAR(30) NOT NULL DEFAULT 'pendente',
	valor_orcamento NUMERIC(10, 2),
	prazo_estimado_dias INTEGER,
	cliente_id INTEGER NOT NULL,
	tecnico_id INTEGER,
	servico_id INTEGER NOT NULL,
	criado_em DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6),
	atualizado_em DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6),
	FOREIGN KEY(cliente_id) REFERENCES usuarios (id) ON DELETE CASCADE,
	FOREIGN KEY(servico_id) REFERENCES servicos (id) ON DELETE CASCADE,
	FOREIGN KEY(tecnico_id) REFERENCES usuarios (id) ON DELETE CASCADE,
	PRIMARY KEY (id)
)ENGINE=InnoDB CHARSET=utf8mb4 COLLATE utf8mb4_0900_as_ci;

CREATE TABLE avaliacoes (
	id INTEGER NOT NULL AUTO_INCREMENT,
	servico_id INTEGER NOT NULL,
	autor_id INTEGER NOT NULL,
	avaliado_id INTEGER NOT NULL,
	nota INTEGER NOT NULL,
	nota_tempo INTEGER,
	nota_honestidade INTEGER,
	nota_preco_justo INTEGER,
	nota_comportamento INTEGER,
	nota_colaboracao INTEGER,
	comentario TEXT,
	criado_em DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6),
	CONSTRAINT uq_avaliacao_servico_autor UNIQUE (servico_id, autor_id),
	FOREIGN KEY(autor_id) REFERENCES usuarios (id) ON DELETE CASCADE,
	FOREIGN KEY(avaliado_id) REFERENCES usuarios (id) ON DELETE CASCADE,
	FOREIGN KEY(servico_id) REFERENCES servicos (id) ON DELETE CASCADE,
	PRIMARY KEY (id)
)ENGINE=InnoDB CHARSET=utf8mb4 COLLATE utf8mb4_0900_as_ci;

CREATE TABLE diplomas (
	id INTEGER NOT NULL AUTO_INCREMENT,
	perfil_tecnico_id INTEGER NOT NULL,
	arquivo VARCHAR(255) NOT NULL,
	enviado_em DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6),
	FOREIGN KEY(perfil_tecnico_id) REFERENCES perfis_tecnicos (id) ON DELETE CASCADE,
	PRIMARY KEY (id)
)ENGINE=InnoDB CHARSET=utf8mb4 COLLATE utf8mb4_0900_as_ci;

CREATE TABLE fotos_servicos (
	id INTEGER NOT NULL AUTO_INCREMENT,
	servico_id INTEGER NOT NULL,
	arquivo VARCHAR(255) NOT NULL,
	enviado_em DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6),
	FOREIGN KEY(servico_id) REFERENCES servicos (id) ON DELETE CASCADE,
	PRIMARY KEY (id)
)ENGINE=InnoDB CHARSET=utf8mb4 COLLATE utf8mb4_0900_as_ci;

CREATE TABLE historico_servicos (
	id INTEGER NOT NULL AUTO_INCREMENT,
	servico_id INTEGER NOT NULL,
	status_anterior VARCHAR(30),
	status_novo VARCHAR(30) NOT NULL,
	alterado_por_id INTEGER,
	alterado_em DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6),
	FOREIGN KEY(alterado_por_id) REFERENCES usuarios (id) ON DELETE SET NULL,
	FOREIGN KEY(servico_id) REFERENCES servicos (id) ON DELETE CASCADE,
	PRIMARY KEY (id)
)ENGINE=InnoDB CHARSET=utf8mb4 COLLATE utf8mb4_0900_as_ci;

CREATE TABLE mensagens_chamado (
	id INTEGER NOT NULL AUTO_INCREMENT,
	servico_id INTEGER NOT NULL,
	autor_id INTEGER NOT NULL,
	conteudo TEXT NOT NULL,
	lida_em DATETIME(6),
	criado_em DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6),
	FOREIGN KEY(autor_id) REFERENCES usuarios (id) ON DELETE CASCADE,
	FOREIGN KEY(servico_id) REFERENCES servicos (id) ON DELETE CASCADE,
	PRIMARY KEY (id)
)ENGINE=InnoDB CHARSET=utf8mb4 COLLATE utf8mb4_0900_as_ci;

CREATE INDEX ix_mensagens_chamado_servico_id ON mensagens_chamado (servico_id);

CREATE TABLE notificacoes (
	id INTEGER NOT NULL AUTO_INCREMENT,
	usuario_id INTEGER NOT NULL,
	servico_id INTEGER,
	papel VARCHAR(10) NOT NULL,
	tipo VARCHAR(40) NOT NULL,
	titulo VARCHAR(120) NOT NULL,
	mensagem VARCHAR(300) NOT NULL,
	lida_em DATETIME(6),
	criado_em DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6),
	FOREIGN KEY(servico_id) REFERENCES servicos (id) ON DELETE CASCADE,
	FOREIGN KEY(usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE,
	PRIMARY KEY (id)
)ENGINE=InnoDB CHARSET=utf8mb4 COLLATE utf8mb4_0900_as_ci;

CREATE INDEX ix_notificacoes_usuario_id ON notificacoes (usuario_id);

CREATE TABLE solicitacoes_aprovacao (
	id INTEGER NOT NULL AUTO_INCREMENT,
	servico_id INTEGER NOT NULL,
	tecnico_id INTEGER NOT NULL,
	descricao TEXT NOT NULL,
	valor_adicional NUMERIC(10, 2) NOT NULL,
	status VARCHAR(20) NOT NULL DEFAULT 'pendente',
	justificativa_recusa TEXT,
	criado_em DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6),
	respondido_em DATETIME(6),
	FOREIGN KEY(servico_id) REFERENCES servicos (id) ON DELETE CASCADE,
	FOREIGN KEY(tecnico_id) REFERENCES usuarios (id) ON DELETE CASCADE,
	PRIMARY KEY (id)
)ENGINE=InnoDB CHARSET=utf8mb4 COLLATE utf8mb4_0900_as_ci;

CREATE TABLE solicitacoes_tecnicos (
	id INTEGER NOT NULL AUTO_INCREMENT,
	servico_id INTEGER NOT NULL,
	tecnico_id INTEGER NOT NULL,
	status VARCHAR(20) NOT NULL DEFAULT 'pendente',
	criado_em DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6),
	respondido_em DATETIME(6),
	FOREIGN KEY(servico_id) REFERENCES servicos (id) ON DELETE CASCADE,
	FOREIGN KEY(tecnico_id) REFERENCES usuarios (id) ON DELETE CASCADE,
	PRIMARY KEY (id)
)ENGINE=InnoDB CHARSET=utf8mb4 COLLATE utf8mb4_0900_as_ci;
