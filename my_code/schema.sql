DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS user_playlists;

CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL
);

CREATE TABLE user_playlists (
  user_id INTEGER,
  playlist_name TEXT NOT NULL,
  playlist_url TEXT NOT NULL,
  PRIMARY KEY (user_id, playlist_url),
  FOREIGN KEY (user_id) REFERENCES user(id)
  
);
