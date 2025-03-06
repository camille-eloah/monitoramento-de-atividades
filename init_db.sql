CREATE DATABASE IF NOT EXISTS db_monitoramento;
USE db_monitoramento;

create table if not exists tb_disciplinas (
    dis_id integer auto_increment primary key,
    dis_nome VARCHAR(100) not null,
    dis_prof_responsavel VARCHAR(100) not null,
    dis_carga_hr int not null
);

create table if not exists tb_alunos (
    alu_id integer auto_increment primary key,
    alu_nome VARCHAR(50) not null,
    alu_matricula text not null unique,
    alu_email VARCHAR(100) not null unique,
    alu_curso VARCHAR(50) not null,
    alu_data_nasc date not null
);

create table if not exists tb_professores (
    prof_id integer auto_increment primary key,
    prof_nome VARCHAR(50) not null,
    prof_email VARCHAR(100) not null unique,
    prof_senha VARCHAR(255) not null

);

create table if not exists tb_aulas (
    aul_id integer auto_increment primary key,
    aul_descricao VARCHAR(200) not null,
    aul_data datetime not null,
    aul_prof_id integer not null,
    aul_dis_id integer not null,
    foreign key (aul_prof_id) references tb_professores(prof_id) ON DELETE CASCADE,
    foreign key (aul_dis_id) references tb_disciplinas(dis_id) ON DELETE CASCADE
);

create table if not exists tb_alunos_disciplinas (
    ad_id integer auto_increment primary key,
    ad_alu_id integer not null,
    ad_dis_id integer not null,
    foreign key (ad_alu_id) references tb_alunos(alu_id) ON DELETE CASCADE,
    foreign key (ad_dis_id) references tb_disciplinas(dis_id) ON DELETE CASCADE 
);

create table if not exists tb_cursos (
    cur_id integer auto_increment primary key,
    cur_nome VARCHAR(100) not null,
    cur_descricao VARCHAR(255)
);

create table if not exists tb_cursos_disciplinas (
    cd_id integer auto_increment primary key,
    cd_cur_id integer not null,
    cd_dis_id integer not null,
    foreign key (cd_cur_id) references tb_cursos(cur_id) ON DELETE CASCADE,
    foreign key (cd_dis_id) references tb_disciplinas(dis_id) ON DELETE CASCADE
);

create table if not exists tb_atividades (
    ati_id integer auto_increment primary key,
    ati_dis_id integer not null,
    ati_tipo VARCHAR(200) not null,
    ati_descricao VARCHAR(200) not null,
    ati_data_entrega datetime not null,
    ati_peso int not null,
    foreign key (ati_dis_id) references tb_disciplinas(dis_id) ON DELETE CASCADE
);

CREATE TABLE if not exists tb_aula_frequencia (
    freq_id INT AUTO_INCREMENT PRIMARY KEY,
    freq_aula_id INT NOT NULL,
    freq_alu_id INT NOT NULL,
    freq_frequencia INT NOT NULL,
    FOREIGN KEY (freq_aula_id) REFERENCES tb_aulas(aul_id) ON DELETE CASCADE,
    FOREIGN KEY (freq_alu_id) REFERENCES tb_alunos(alu_id) ON DELETE CASCADE
);

CREATE TABLE if not exists tb_aluno_atividade (
    alunoativ_id INT AUTO_INCREMENT PRIMARY KEY,
    alunoativ_alu_id integer not null,
    alunoativ_ati_id integer not null,
	alunoativ_data_entrega DATETIME not null,
    alunoativ_situacao ENUM('Pendente', 'Em andamento', 'Entregue') NOT NULL,
    alunoativ_nota FLOAT not null,
    foreign key (alunoativ_alu_id) references tb_alunos(alu_id) ON DELETE CASCADE,
    foreign key (alunoativ_ati_id) references tb_atividades(ati_id) ON DELETE CASCADE


);

CREATE TABLE IF NOT EXISTS tb_aluno_media (
    media_id INT AUTO_INCREMENT PRIMARY KEY,
    media_alu_id INT NOT NULL,
    media_dis_id INT NOT NULL,
    media_calculada FLOAT NOT NULL,
    FOREIGN KEY (media_alu_id) REFERENCES tb_alunos(alu_id) ON DELETE CASCADE,
    FOREIGN KEY (media_dis_id) REFERENCES tb_disciplinas(dis_id) ON DELETE CASCADE,
    UNIQUE (media_alu_id, media_dis_id)  -- Garantindo que cada aluno tenha apenas uma média por disciplina
);


CREATE TABLE IF NOT EXISTS logs_notas (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    operacao VARCHAR(10),  -- Tipo de operação: INSERT, UPDATE ou DELETE
    aluno_id INT,
    disciplina_id INT,
    nota FLOAT,
    data_operacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tipo_avaliacao VARCHAR(200),
    peso INT
);

------------------------------
-- NÃO ESTÁ FUNCIONANDO NO INIT_DB.SQL! SÓ FUNCIONA NO MYSQL WORKBENCH:
------------------------------

-- ---------------- FUNÇÕES, TRIGGERS E PROCEDURES ------------------ 
-- ---------------------------------------------------------------------- 
-- 1. CALCULAR_MEDIA (calcula média do aluno em uma disciplina, pegando as notas de todas as atividades referentes a essa disciplina)
-- ---------------------------------------------------------------------- 
-- EXEMPLO DE USO: Suponha que você queira calcular a média do aluno com ID 1 na disciplina com ID 1
-- SELECT calcular_media(1, 1) AS media_aluno_disciplina;

-- EXEMPLO DE USO 2:
-- SELECT 
--    a.alu_nome AS nome_aluno,
--    d.dis_nome AS nome_disciplina,
--    calcular_media(a.alu_id, d.dis_id) AS media_aluno_disciplina
-- FROM 
--    tb_alunos a
-- JOIN 
--    tb_alunos_disciplinas ad ON a.alu_id = ad.ad_alu_id
-- JOIN 
--    tb_disciplinas d ON ad.ad_dis_id = d.dis_id
-- WHERE 
--    a.alu_id = 1
-- AND 
--    d.dis_id = 1;

DROP FUNCTION IF EXISTS calcular_media;

DELIMITER $$

CREATE FUNCTION calcular_media(id_aluno INT, id_disciplina INT) 
RETURNS FLOAT
DETERMINISTIC
BEGIN
    DECLARE total_notas FLOAT DEFAULT 0;
    DECLARE total_peso INT DEFAULT 0;
    DECLARE media FLOAT;

    -- Calcula a soma das notas ponderadas e o peso total
    SELECT SUM(a.alunoativ_nota * b.ati_peso), SUM(b.ati_peso)
    INTO total_notas, total_peso
    FROM tb_aluno_atividade a
    JOIN tb_atividades b ON a.alunoativ_ati_id = b.ati_id
    WHERE a.alunoativ_alu_id = id_aluno
    AND b.ati_dis_id = id_disciplina
    AND a.alunoativ_situacao = 'Entregue';

    -- Calcula a média ponderada
    IF total_peso > 0 THEN
        SET media = total_notas / total_peso;
    ELSE
        SET media = 0;  -- Caso não haja atividades entregues ou peso, a média é 0
    END IF;

    -- Registra ou atualiza a média na tabela tb_aluno_media
    INSERT INTO tb_aluno_media (media_alu_id, media_dis_id, media_calculada)
    VALUES (id_aluno, id_disciplina, media)
    ON DUPLICATE KEY UPDATE media_calculada = media;  -- Se já existir um registro, atualiza a média

    RETURN media;
END $$

DELIMITER ;

-- ---------------------------------------------------------------------- 
-- 2. REGISTRAR_NOTA (registra nota do aluno em uma atividade)
-- ---------------------------------------------------------------------- 
-- EXEMPLO DE USO: registrar_nota(id_aluno, id_disciplina, nota, tipo_avaliacao, peso)
-- CALL registrar_nota(1, 1, 95, 'Prova 4', 50);

DELIMITER $$

CREATE PROCEDURE registrar_nota(
    IN id_aluno INT,
    IN id_disciplina INT,
    IN nota FLOAT,
    IN tipo_avaliacao VARCHAR(200),
    IN peso INT  -- Adicionando o parâmetro de peso
)
BEGIN
    DECLARE atividade_id INT;
    DECLARE nota_existente FLOAT;

    -- Verifica se já existe uma atividade para a disciplina com o tipo de avaliação fornecido
    SELECT ati_id
    INTO atividade_id
    FROM tb_atividades
    WHERE ati_dis_id = id_disciplina
    AND ati_tipo = tipo_avaliacao
    LIMIT 1;

    -- Se a atividade não existir, cria uma nova
    IF atividade_id IS NULL THEN
        -- Insere uma nova atividade com o peso especificado
        INSERT INTO tb_atividades(ati_dis_id, ati_tipo, ati_peso, ati_descricao, ati_data_entrega)
        VALUES (id_disciplina, tipo_avaliacao, peso, CONCAT(tipo_avaliacao, ' para ', (SELECT dis_nome FROM tb_disciplinas WHERE dis_id = id_disciplina)), NOW());
        
        -- Recupera o id da atividade recém-criada
        SET atividade_id = LAST_INSERT_ID();
    END IF;

    -- Verifica se o aluno já tem uma nota registrada para essa atividade
    SELECT alunoativ_nota
    INTO nota_existente
    FROM tb_aluno_atividade
    WHERE alunoativ_alu_id = id_aluno
    AND alunoativ_ati_id = atividade_id
    LIMIT 1;

    -- Se a nota já existir, atualiza a nota
    IF nota_existente IS NOT NULL THEN
        UPDATE tb_aluno_atividade
        SET alunoativ_nota = nota
        WHERE alunoativ_alu_id = id_aluno
        AND alunoativ_ati_id = atividade_id;
    ELSE
        -- Caso contrário, insere a nota
        INSERT INTO tb_aluno_atividade(alunoativ_alu_id, alunoativ_ati_id, alunoativ_nota, alunoativ_situacao, alunoativ_data_entrega)
        VALUES (id_aluno, atividade_id, nota, 'Entregue', NOW());
    END IF;

END $$

DELIMITER ;

-- ---------------------------------------------------------------------- 
-- 3. VERIFICAR FREQUÊNCIA (impede calcular_media caso a frequência do aluno na disciplina seja menor que 75%)
-- ---------------------------------------------------------------------- 

DROP TRIGGER IF EXISTS verificar_frequencia;

DELIMITER $$

CREATE TRIGGER verificar_frequencia
BEFORE INSERT ON tb_aluno_media
FOR EACH ROW
BEGIN
    DECLARE total_aulas INT;
    DECLARE aulas_presentes INT;
    DECLARE frequencia_percentual FLOAT;

    -- Calcula o total de aulas e o total de frequências presentes do aluno na disciplina
    SELECT COUNT(*) INTO total_aulas
    FROM tb_aulas
    WHERE aul_dis_id = NEW.media_dis_id;  -- Disciplina relacionada ao aluno

    SELECT COUNT(*) INTO aulas_presentes
    FROM tb_aula_frequencia af
    JOIN tb_aulas a ON af.freq_aula_id = a.aul_id
    WHERE af.freq_alu_id = NEW.media_alu_id  -- Aluno relacionado à frequência
    AND af.freq_frequencia = 1
    AND a.aul_dis_id = NEW.media_dis_id;  -- Disciplina relacionada à aula

    -- Calcula o percentual de frequência
    IF total_aulas > 0 THEN
        SET frequencia_percentual = (aulas_presentes / total_aulas) * 100;
    ELSE
        SET frequencia_percentual = 0;  -- Se não houver aulas, a frequência é considerada 0
    END IF;

    -- Verifica se a frequência é menor que 75% e impede o cálculo da média
    IF frequencia_percentual < 75 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Frequência insuficiente para calcular a média (menor que 75%)';
    END IF;
END $$

DELIMITER ;

-- ---------------------------------------------------------------------- 
-- 4. LOG_NOTAS (registra inserção, edição e exclusão de notas na tabela logs_notas)
-- ---------------------------------------------------------------------- 

DROP TRIGGER IF EXISTS log_notas;

DELIMITER $$

CREATE TRIGGER log_notas
AFTER INSERT ON tb_aluno_atividade
FOR EACH ROW
BEGIN
    -- Registro de inserção de nota
    INSERT INTO logs_notas (operacao, aluno_id, disciplina_id, nota, tipo_avaliacao, peso)
    VALUES ('INSERT', NEW.alunoativ_alu_id, (SELECT ati_dis_id FROM tb_atividades WHERE ati_id = NEW.alunoativ_ati_id), NEW.alunoativ_nota, 
            (SELECT ati_tipo FROM tb_atividades WHERE ati_id = NEW.alunoativ_ati_id), 
            (SELECT ati_peso FROM tb_atividades WHERE ati_id = NEW.alunoativ_ati_id));
END $$

DELIMITER ;

DELIMITER $$

CREATE TRIGGER log_notas_update
AFTER UPDATE ON tb_aluno_atividade
FOR EACH ROW
BEGIN
    -- Registro de atualização de nota
    INSERT INTO logs_notas (operacao, aluno_id, disciplina_id, nota, tipo_avaliacao, peso)
    VALUES ('UPDATE', NEW.alunoativ_alu_id, (SELECT ati_dis_id FROM tb_atividades WHERE ati_id = NEW.alunoativ_ati_id), NEW.alunoativ_nota, 
            (SELECT ati_tipo FROM tb_atividades WHERE ati_id = NEW.alunoativ_ati_id), 
            (SELECT ati_peso FROM tb_atividades WHERE ati_id = NEW.alunoativ_ati_id));
END $$

DELIMITER ;

DELIMITER $$

CREATE TRIGGER log_notas_delete
AFTER DELETE ON tb_aluno_atividade
FOR EACH ROW
BEGIN
    -- Registro de exclusão de nota
    INSERT INTO logs_notas (operacao, aluno_id, disciplina_id, nota, tipo_avaliacao, peso)
    VALUES ('DELETE', OLD.alunoativ_alu_id, (SELECT ati_dis_id FROM tb_atividades WHERE ati_id = OLD.alunoativ_ati_id), OLD.alunoativ_nota, 
            (SELECT ati_tipo FROM tb_atividades WHERE ati_id = OLD.alunoativ_ati_id), 
            (SELECT ati_peso FROM tb_atividades WHERE ati_id = OLD.alunoativ_ati_id));
END $$

DELIMITER ;