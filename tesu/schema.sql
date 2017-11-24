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

