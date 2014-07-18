
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ref char(40) NOT NULL,
    json text NOT NULL,
    gameat timestamp NOT NULL,
    rulecode char(4) NOT NULL,
    lobby char(4) NOT NULL,
    createat timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
    id_game INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS logs_ref_index on logs(ref);
CREATE INDEX IF NOT EXISTS logs_gameat_index on logs(gameat);
CREATE INDEX IF NOT EXISTS logs_rulecode_index on logs(rulecode);
CREATE INDEX IF NOT EXISTS logs_lobby_index on logs(lobby);
CREATE INDEX IF NOT EXISTS logs_createat_index on logs(createat);
CREATE INDEX IF NOT EXISTS logs_id_game_index on logs(id_game);

CREATE TABLE IF NOT EXISTS logs_name (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ref char(40) NOT NULL,
    name char(40) NOT NULL,
    sex char(1) NOT NULL,
    rate float NOT NULL,
    dan char(16) NOT NULL,
    score INTEGER NOT NULL,
    point INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS logs_name_id_index on logs_name(id);
CREATE INDEX IF NOT EXISTS logs_name_ref_index on logs_name(ref);
CREATE INDEX IF NOT EXISTS logs_name_name_index on logs_name(name);


CREATE TABLE IF NOT EXISTS user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name char(40) NOT NULL,
    password char(64) NOT NULL,
    id_role INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS user_name_index on user(name);
CREATE INDEX IF NOT EXISTS user_id_role_index on user(id_role);

CREATE TABLE IF NOT EXISTS role (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name char(40)
); 

CREATE INDEX IF NOT EXISTS role_name_index on role(name);

CREATE TABLE IF NOT EXISTS right (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name char(40)
);

CREATE TABLE IF NOT EXISTS roleRight (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_role INTEGER NOT NULL,
    id_right INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS roleRight_id_role_index on roleRight(id_role);
CREATE INDEX IF NOT EXISTS roleRight_id_right_index on roleRight(id_right);

CREATE TABLE IF NOT EXISTS game (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name char(128) NOT NULL,
    url char(128) NOT NULL,
    id_statue INTEGER NOT NULL DEFAULT 0,
    des text NOT NULL DEFAULT ""
);

CREATE TABLE IF NOT EXISTS gameStatue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name char(40)
);

CREATE TABLE IF NOT EXISTS team (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name char(80),
    id_game INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS team_id_game_index on team(id_game);

CREATE TABLE IF NOT EXISTS teamUser (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_team INTEGER NOT NULL,
    name char(40) NOT NULL
);

CREATE INDEX IF NOT EXISTS teamUser_id_team_index on teamUser(id_team);
CREATE INDEX IF NOT EXISTS teamUser_name_index on teamUser(name);

CREATE TABLE IF NOT EXISTS teamAddon (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_team INTEGER NOT NULL,
    sc float NOT NULL,
    des text NOT NULL
);