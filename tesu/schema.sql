drop table if exists posts;
create table posts (
    id integer primary key autoincrement,
    timestamp datetime default current_timestamp,
    title text not null,
    slug text not null,
    'text' text not null
);

drop table if exists projects;
create table projects (
    id integer primary key autoincrement,
    name text not null,
    description text not null,
    url not null,
    urlname text default 'link'
);

drop table if exists sidebar_games;
create table sidebar_games (
    id integer primary key autoincrement,
    name text not null,
    hours real not null
);

drop table if exists sidebar_anime;
create table sidebar_anime (
    id integer primary key autoincrement,
    name text not null,
    progress text not null
);

drop table if exists sidebar_music;
create table sidebar_music (
    id integer primary key autoincrement,
    artist text not null,
    name text not null
);

