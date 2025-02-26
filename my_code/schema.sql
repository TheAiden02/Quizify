DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS user_playlists;

CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL
);

CREATE TABLE user_playlists (
  user_id INTEGER,
  playlist_name TEXT UNIQUE NOT NULL,
  playlist_url TEXT UNIQUE NOT NULL,
  FOREIGN KEY (user_id) REFERENCES user(id)
  
);
