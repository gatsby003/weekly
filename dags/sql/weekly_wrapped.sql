CREATE TABLE IF NOT EXISTS weekly_wrapped (
    user_id INTEGER REFERENCES users (id),
    wrapped JSON,
    time_added DATE DEFAULT CURRENT_DATE
);