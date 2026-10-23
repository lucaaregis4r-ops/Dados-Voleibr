-- Schema definition for CBV Volley Data DuckDB database

CREATE TABLE IF NOT EXISTS matches (
    match_id BIGINT PRIMARY KEY,
    date DATE,
    time_str VARCHAR,
    competition VARCHAR,
    category VARCHAR,
    gender VARCHAR,
    season VARCHAR,
    home_team VARCHAR,
    away_team VARCHAR,
    home_sets INTEGER,
    away_sets INTEGER,
    validation_status VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS upcoming_matches (
    match_id BIGINT PRIMARY KEY,
    competition VARCHAR,
    category VARCHAR,
    gender VARCHAR,
    season VARCHAR,
    round_name VARCHAR,
    match_date VARCHAR,
    match_time VARCHAR,
    home_team VARCHAR,
    away_team VARCHAR,
    gym VARCHAR,
    predicted_winner VARCHAR,
    predicted_prob_home DOUBLE,
    predicted_prob_away DOUBLE,
    projected_score VARCHAR,
    confidence VARCHAR,
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

CREATE TABLE IF NOT EXISTS team_tactical_stats (
    match_id BIGINT,
    team VARCHAR,
    sideout_points INTEGER,
    sideout_receptions INTEGER,
    sideout_rate DOUBLE,
    breakpoint_points INTEGER,
    breakpoint_serves INTEGER,
    breakpoint_rate DOUBLE,
    p1_diff INTEGER,
    p2_diff INTEGER,
    p3_diff INTEGER,
    p4_diff INTEGER,
    p5_diff INTEGER,
    p6_diff INTEGER,
    pos_rec_att_attempts INTEGER,
    pos_rec_att_points INTEGER,
    pos_rec_att_points_pct DOUBLE,
    pos_rec_att_blocked INTEGER,
    pos_rec_att_errors INTEGER,
    pos_rec_att_efficiency_pct DOUBLE,
    neg_rec_att_attempts INTEGER,
    neg_rec_att_points INTEGER,
    neg_rec_att_points_pct DOUBLE,
    neg_rec_att_blocked INTEGER,
    neg_rec_att_errors INTEGER,
    neg_rec_att_efficiency_pct DOUBLE,
    trans_att_attempts INTEGER,
    trans_att_points INTEGER,
    trans_att_points_pct DOUBLE,
    trans_att_blocked INTEGER,
    trans_att_errors INTEGER,
    trans_att_efficiency_pct DOUBLE,
    PRIMARY KEY (match_id, team)
);

CREATE TABLE IF NOT EXISTS set_tactical_stats (
    match_id BIGINT,
    team VARCHAR,
    set_number INTEGER,
    serve_points_won INTEGER,
    attack_points_won INTEGER,
    block_points_won INTEGER,
    opponent_errors_won INTEGER,
    serve_total INTEGER,
    serve_errors INTEGER,
    serve_aces INTEGER,
    reception_total INTEGER,
    reception_errors INTEGER,
    reception_positive_pct DOUBLE,
    reception_excellent_pct DOUBLE,
    attack_total INTEGER,
    attack_errors INTEGER,
    attack_blocked INTEGER,
    attack_points INTEGER,
    attack_points_pct DOUBLE,
    PRIMARY KEY (match_id, team, set_number)
);


CREATE TABLE IF NOT EXISTS metric_definitions (
    metric_key VARCHAR PRIMARY KEY, display_name VARCHAR, description VARCHAR,
    formula VARCHAR, metric_class VARCHAR, source_level VARCHAR,
    minimum_sample INTEGER, version VARCHAR
);
CREATE TABLE IF NOT EXISTS match_provenance (
    match_id BIGINT PRIMARY KEY, source_url VARCHAR, source_document_id VARCHAR,
    fetched_at TIMESTAMP, parser_version VARCHAR, data_version VARCHAR
);
-- Empty until a verified event source is available; aggregate reports cannot fill these.
CREATE TABLE IF NOT EXISTS rallies (
    rally_id VARCHAR PRIMARY KEY, match_id BIGINT, set_number INTEGER,
    rally_number INTEGER, serving_team VARCHAR, receiving_team VARCHAR,
    winner_team VARCHAR, rotation_home INTEGER, rotation_away INTEGER,
    score_home_before INTEGER, score_away_before INTEGER
);
CREATE TABLE IF NOT EXISTS contacts (
    rally_id VARCHAR, sequence_index INTEGER, team VARCHAR, player_id VARCHAR,
    skill VARCHAR, evaluation VARCHAR, zone_start VARCHAR, zone_end VARCHAR,
    phase VARCHAR, setter_position INTEGER, attack_tempo VARCHAR,
    PRIMARY KEY(rally_id, sequence_index)
);
