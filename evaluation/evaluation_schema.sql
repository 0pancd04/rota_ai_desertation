-- Evaluation schema for results, comparisons, user studies, and performance
-- This file can be applied to data/rota_operations.db

PRAGMA foreign_keys = ON;

-- Datasets used in evaluations (e.g., a particular week or site)
CREATE TABLE IF NOT EXISTS evaluation_datasets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    num_patients INTEGER,
    num_employees INTEGER,
    start_date TEXT,
    end_date TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Individual runs (baseline manual schedule vs AI/Core engine)
CREATE TABLE IF NOT EXISTS evaluation_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dataset_id INTEGER NOT NULL,
    run_label TEXT NOT NULL,             -- e.g., "Manual-Baseline-Week12", "AI-Core-Week12"
    engine_type TEXT NOT NULL,           -- 'baseline' | 'ai_core' | 'legacy_ai'
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (dataset_id) REFERENCES evaluation_datasets(id)
);

-- Optional import of manual baseline schedule for direct A/B comparisons
CREATE TABLE IF NOT EXISTS baseline_assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dataset_id INTEGER NOT NULL,
    employee_id TEXT NOT NULL,
    employee_name TEXT NOT NULL,
    patient_id TEXT NOT NULL,
    patient_name TEXT NOT NULL,
    service_type TEXT NOT NULL,
    start_time TEXT,
    end_time TEXT,
    duration INTEGER,                    -- minutes
    travel_time INTEGER,                 -- minutes (if available)
    source TEXT,                         -- e.g., 'uploaded_excel'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (dataset_id) REFERENCES evaluation_datasets(id)
);

-- Metrics captured per run (flexible key/value storage)
CREATE TABLE IF NOT EXISTS evaluation_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    metric_name TEXT NOT NULL,           -- e.g., 'qualification_match_accuracy', 'avg_travel_minutes', ...
    metric_value REAL NOT NULL,
    unit TEXT,                           -- e.g., '%', 'minutes', 'count'
    details_json TEXT,                   -- arbitrary JSON payload for drill-down
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(run_id, metric_name),
    FOREIGN KEY (run_id) REFERENCES evaluation_runs(id)
);

-- Direct baseline vs AI comparison rows per metric
CREATE TABLE IF NOT EXISTS evaluation_comparisons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dataset_id INTEGER NOT NULL,
    baseline_run_id INTEGER NOT NULL,
    ai_run_id INTEGER NOT NULL,
    metric_name TEXT NOT NULL,
    baseline_value REAL,
    ai_value REAL,
    difference REAL,                     -- ai_value - baseline_value
    pct_improvement REAL,                -- (baseline - ai) / baseline
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (dataset_id) REFERENCES evaluation_datasets(id),
    FOREIGN KEY (baseline_run_id) REFERENCES evaluation_runs(id),
    FOREIGN KEY (ai_run_id) REFERENCES evaluation_runs(id)
);

-- Constraint violations per run (e.g., overlap, qualification, language, max travel)
CREATE TABLE IF NOT EXISTS constraint_violations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    violation_type TEXT NOT NULL,        -- 'overlap' | 'qualification' | 'language' | 'max_travel' | 'break'
    count INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (run_id) REFERENCES evaluation_runs(id)
);

-- User study responses including SUS (System Usability Scale)
CREATE TABLE IF NOT EXISTS user_study_responses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    participant_id TEXT,
    role TEXT,                           -- e.g., 'nurse', 'scheduler', 'manager'
    experience_years INTEGER,
    sus_q1 INTEGER, sus_q2 INTEGER, sus_q3 INTEGER, sus_q4 INTEGER, sus_q5 INTEGER,
    sus_q6 INTEGER, sus_q7 INTEGER, sus_q8 INTEGER, sus_q9 INTEGER, sus_q10 INTEGER,
    sus_score REAL,                      -- 0..100 after scoring
    feedback TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- System performance measurements (e.g., schedule generation time, API latencies)
CREATE TABLE IF NOT EXISTS system_performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scenario TEXT NOT NULL,              -- e.g., 'weekly_rota_generation', 'stats_endpoint'
    metric_name TEXT NOT NULL,           -- e.g., 'duration', 'p95_latency'
    metric_value REAL NOT NULL,
    unit TEXT,                           -- e.g., 'seconds', 'ms'
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Statistical test registry for documented hypothesis testing
CREATE TABLE IF NOT EXISTS statistical_tests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dataset_id INTEGER,
    hypothesis TEXT NOT NULL,            -- e.g., 'H2: travel reduction >= 15%'
    test_name TEXT NOT NULL,             -- 't-test', 'wilcoxon', 'chi-squared', 'z-test'
    sample_size INTEGER,
    p_value REAL,
    effect_size REAL,                    -- e.g., Cohen's d
    ci_low REAL,
    ci_high REAL,
    alpha REAL,                          -- significance level
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    details_json TEXT,
    FOREIGN KEY (dataset_id) REFERENCES evaluation_datasets(id)
);


