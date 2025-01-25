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
    alu_data_nasc datetime not null
);

create table if not exists tb_professores (
    prof_id integer auto_increment primary key,
    prof_nome VARCHAR(50) not null,
    prof_email VARCHAR(100) not null unique,
    prof_senha VARCHAR(50) not null

);

create table if not exists tb_aulas (
    aul_id integer auto_increment primary key,
    aul_descricao VARCHAR(200) not null,
    aul_data datetime not null,
    foreign key (aul_id) references tb_professores(prof_id),
    foreign key (aul_id) references tb_disciplinas(dis_id)
);

create table if not exists tb_alunos_disciplinas (
    ad_id integer auto_increment primary key,
    alu_id integer not null,
    dis_id integer not null,
    foreign key (alu_id) references tb_alunos(alu_id),
    foreign key (dis_id) references tb_disciplinas(dis_id) 
);


create table if not exists tb_atividades (
    ati_id integer auto_increment primary key,
    dis_id integer not null,
    ati_tipo VARCHAR(200) not null,
    ati_descricao VARCHAR(200) not null,
    ati_data_entrega datetime not null,
    ati_peso int not null,
    foreign key (dis_id) references tb_disciplinas(dis_id)
);


create table if not exists tb_frequencia (
    fre_id integer auto_increment primary key,
    dis_id integer not null,
    alu_id integer not null,
    fre_tipo varchar(50) not null,
    fre_quantidade integer not null,
    foreign key (dis_id) references tb_disciplinas(dis_id),
    foreign key (alu_id) references tb_alunos(alu_id) 
);



