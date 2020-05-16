CREATE TABLE posts (
    id integer primary key autoincrement,
    timestamp datetime default current_timestamp,
    title text not null,
    slug text not null,
    'text' text not null
);
CREATE TABLE sqlite_sequence(name,seq);
CREATE TABLE sidebar_games (
id integer primary key autoincrement,
name text not null,
hours real not null
);
CREATE TABLE sidebar_anime (
id integer primary key autoincrement,
name text not null,
progress text not null
);
CREATE TABLE sidebar_music (
id integer primary key autoincrement,
artist text not null,
name text not null
);
CREATE TABLE IF NOT EXISTS "projects" (
    id integer primary key autoincrement,
    name text not null,
    description text not null,
    url text not null,
    urlname text not null,
    img text not null
);
