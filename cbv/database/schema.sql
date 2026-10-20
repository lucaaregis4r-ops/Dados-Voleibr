-- Schema definition for CBV Volley Data DuckDB database

CREATE TABLE IF NOT EXISTS matches (
    match_id BIGINT PRIMARY KEY,
    date DATE,
    time_str VARCHAR,
    competition VARCHAR,
    category VARCHAR,
    gender VARCHAR,
    home_team VARCHAR,
    away_team VARCHAR,
    home_sets INTEGER,
    away_sets INTEGER,
    validation_status VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sets (
    match_id BIGINT,
    set_number INTEGER,
    home_points INTEGER,
    away_points INTEGER,
    duration_minutes INTEGER,
    partial_scores VARCHAR,
    PRIMARY KEY (match_id, set_number)
);

CREATE TABLE IF NOT EXISTS player_match_stats (
    match_id BIGINT,
    team VARCHAR,
    player_number INTEGER,
    player_name VARCHAR,
    is_libero BOOLEAN,
    rating DOUBLE,
    points_total INTEGER,
    break_points INTEGER,
    win_loss INTEGER,
    serve_attempts INTEGER,
    serve_errors INTEGER,
    serve_points INTEGER,
    reception_attempts INTEGER,
    reception_errors INTEGER,
    reception_positive_pct DOUBLE,
    reception_excellent_pct DOUBLE,
    attack_attempts INTEGER,
    attack_errors INTEGER,
    attack_blocked INTEGER,
    attack_points INTEGER,
    attack_points_pct DOUBLE,
    block_points INTEGER,
    PRIMARY KEY (match_id, team, player_number, player_name)
);

CREATE TABLE IF NOT EXISTS team_match_stats (
    match_id BIGINT,
    team VARCHAR,
    coach VARCHAR,
    assistant VARCHAR,
    points_total INTEGER,
    break_points INTEGER,
    win_loss INTEGER,
    serve_attempts INTEGER,
    serve_errors INTEGER,
    serve_points INTEGER,
    reception_attempts INTEGER,
    reception_errors INTEGER,
    reception_positive_pct DOUBLE,
    reception_excellent_pct DOUBLE,
    attack_attempts INTEGER,
    attack_errors INTEGER,
    attack_blocked INTEGER,
    attack_points INTEGER,
    attack_points_pct DOUBLE,
    block_points INTEGER,
    opponent_errors INTEGER,
    PRIMARY KEY (match_id, team)
);
