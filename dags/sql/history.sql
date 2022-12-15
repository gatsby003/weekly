CREATE TABLE IF NOT EXISTS history (
    user_id INTEGER REFERENCES users (id),
    name TEXT,
    played_at TIMESTAMPTZ,
    album_name TEXT,
    artist_name TEXT
);