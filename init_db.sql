create database db_monitoramento;
use db_monitoramento;


create table if not exists tb_disciplinas (
    dis_id integer auto_increment primary key,
    dis_nome VARCHAR(100) not null,
    dis_prof_responsavel VARCHAR(100) not null,
    dis_carga_hr int not null
);

create table if not exists tb_alunos (
    alu_id integer auto_increment primary key,
    alu_nome VARCHAR(50) not null,
    alu_matricula int not null unique,
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
    foreign key (aul_prof_id) references tb_professores(prof_id),
    foreign key (aul_dis_id) references tb_disciplinas(dis_id)
);

create table if not exists tb_alunos_disciplinas (
    ad_id integer auto_increment primary key,
    ad_alu_id integer not null,
    ad_dis_id integer not null,
    foreign key (ad_alu_id) references tb_alunos(alu_id),
    foreign key (ad_dis_id) references tb_disciplinas(dis_id) 
);

create table if not exists tb_cursos (
    cur_id integer auto_increment primary key,
    cur_nome VARCHAR(100) not null,
    cur_descricao VARCHAR(255)
);


create table if not exists tb_cursos_disciplinas (
    cd_id integer auto_increment primary key,
    cd_cur_id integer not null,
    cd_dis_id integer not null,0
    foreign key (cd_cur_id) references tb_cursos(cur_id),
    foreign key (cd_dis_id) references tb_disciplinas(dis_id)
);


create table if not exists tb_atividades (
    ati_id integer auto_increment primary key,
    ati_dis_id integer not null,
    ati_tipo VARCHAR(200) not null,
    ati_descricao VARCHAR(200) not null,
    ati_data_entrega datetime not null,
    ati_peso int not null,
    foreign key (ati_dis_id) references tb_disciplinas(dis_id)
);

CREATE TABLE tb_aula_frequencia (
    freq_id INT AUTO_INCREMENT PRIMARY KEY,
    freq_aula_id INT NOT NULL,
    freq_alu_id INT NOT NULL,
    freq_frequencia INT NOT NULL,
    FOREIGN KEY (freq_aula_id) REFERENCES tb_aulas(aul_id) ON DELETE CASCADE,
    FOREIGN KEY (freq_alu_id) REFERENCES tb_alunos(alu_id) ON DELETE CASCADE
);
