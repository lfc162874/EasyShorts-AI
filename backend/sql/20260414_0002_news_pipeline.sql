-- EasyShorts stage 2 news pipeline DDL
-- Safe to rerun on the same database.

BEGIN;

CREATE TABLE IF NOT EXISTS news_sources (
    id BIGSERIAL PRIMARY KEY,
    source_key VARCHAR(128) NOT NULL,
    name VARCHAR(128) NOT NULL,
    source_type VARCHAR(32) NOT NULL DEFAULT 'RSS',
    url VARCHAR(500) NOT NULL,
    category VARCHAR(64),
    language VARCHAR(16) NOT NULL DEFAULT 'en',
    fetch_interval_minutes INTEGER NOT NULL DEFAULT 360,
    is_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    last_fetched_at TIMESTAMPTZ,
    last_success_at TIMESTAMPTZ,
    last_error_message TEXT,
    extra JSON,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_news_sources_source_key UNIQUE (source_key)
);

CREATE INDEX IF NOT EXISTS ix_news_sources_source_type ON news_sources (source_type);
CREATE INDEX IF NOT EXISTS ix_news_sources_is_enabled ON news_sources (is_enabled);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint c
        WHERE c.conrelid = 'news_sources'::regclass
          AND c.contype = 'u'
          AND pg_get_constraintdef(c.oid) = 'UNIQUE (source_key)'
    ) THEN
        ALTER TABLE news_sources
            ADD CONSTRAINT uq_news_sources_source_key UNIQUE (source_key);
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS news (
    id BIGSERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    content TEXT,
    source VARCHAR(255) NOT NULL,
    source_id BIGINT,
    source_url VARCHAR(500),
    url VARCHAR(500) NOT NULL,
    publish_time TIMESTAMPTZ,
    status VARCHAR(32) NOT NULL DEFAULT 'NEW',
    dedup_hash VARCHAR(128),
    category VARCHAR(64),
    hot_score INTEGER NOT NULL DEFAULT 0,
    language VARCHAR(16) NOT NULL DEFAULT 'en',
    summary TEXT,
    translated_title VARCHAR(500),
    translated_content TEXT,
    script TEXT,
    tags JSON,
    filter_reason TEXT,
    raw_metadata JSON,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_news_url UNIQUE (url)
);

CREATE INDEX IF NOT EXISTS ix_news_status ON news (status);
CREATE INDEX IF NOT EXISTS ix_news_publish_time ON news (publish_time);
CREATE INDEX IF NOT EXISTS ix_news_source_id ON news (source_id);
CREATE INDEX IF NOT EXISTS ix_news_category ON news (category);
CREATE INDEX IF NOT EXISTS ix_news_dedup_hash ON news (dedup_hash);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint c
        WHERE c.conrelid = 'news'::regclass
          AND c.contype = 'u'
          AND pg_get_constraintdef(c.oid) = 'UNIQUE (url)'
    ) THEN
        ALTER TABLE news
            ADD CONSTRAINT uq_news_url UNIQUE (url);
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint c
        WHERE c.conrelid = 'news'::regclass
          AND c.contype = 'f'
          AND pg_get_constraintdef(c.oid) = 'FOREIGN KEY (source_id) REFERENCES news_sources(id) ON DELETE SET NULL'
    ) THEN
        ALTER TABLE news
            ADD CONSTRAINT fk_news_source_id_news_sources
            FOREIGN KEY (source_id) REFERENCES news_sources(id) ON DELETE SET NULL;
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS news_fetch_records (
    id BIGSERIAL PRIMARY KEY,
    source_id BIGINT NOT NULL,
    task_job_id BIGINT,
    request_id VARCHAR(64),
    fetch_mode VARCHAR(32) NOT NULL DEFAULT 'MANUAL',
    status VARCHAR(32) NOT NULL DEFAULT 'PENDING',
    total_count INTEGER NOT NULL DEFAULT 0,
    new_count INTEGER NOT NULL DEFAULT 0,
    duplicate_count INTEGER NOT NULL DEFAULT 0,
    filtered_count INTEGER NOT NULL DEFAULT 0,
    error_count INTEGER NOT NULL DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    extra JSON,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_news_fetch_records_source_id
        FOREIGN KEY (source_id) REFERENCES news_sources(id) ON DELETE CASCADE,
    CONSTRAINT fk_news_fetch_records_task_job_id
        FOREIGN KEY (task_job_id) REFERENCES task_jobs(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS ix_news_fetch_records_source_id ON news_fetch_records (source_id);
CREATE INDEX IF NOT EXISTS ix_news_fetch_records_status ON news_fetch_records (status);
CREATE INDEX IF NOT EXISTS ix_news_fetch_records_request_id ON news_fetch_records (request_id);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint c
        WHERE c.conrelid = 'news_fetch_records'::regclass
          AND c.contype = 'f'
          AND pg_get_constraintdef(c.oid) = 'FOREIGN KEY (source_id) REFERENCES news_sources(id) ON DELETE CASCADE'
    ) THEN
        ALTER TABLE news_fetch_records
            ADD CONSTRAINT fk_news_fetch_records_source_id
            FOREIGN KEY (source_id) REFERENCES news_sources(id) ON DELETE CASCADE;
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint c
        WHERE c.conrelid = 'news_fetch_records'::regclass
          AND c.contype = 'f'
          AND pg_get_constraintdef(c.oid) = 'FOREIGN KEY (task_job_id) REFERENCES task_jobs(id) ON DELETE SET NULL'
    ) THEN
        ALTER TABLE news_fetch_records
            ADD CONSTRAINT fk_news_fetch_records_task_job_id
            FOREIGN KEY (task_job_id) REFERENCES task_jobs(id) ON DELETE SET NULL;
    END IF;
END $$;

ALTER TABLE news ADD COLUMN IF NOT EXISTS source_id BIGINT;
ALTER TABLE news ADD COLUMN IF NOT EXISTS source_url VARCHAR(500);
ALTER TABLE news ADD COLUMN IF NOT EXISTS dedup_hash VARCHAR(128);
ALTER TABLE news ADD COLUMN IF NOT EXISTS category VARCHAR(64);
ALTER TABLE news ADD COLUMN IF NOT EXISTS hot_score INTEGER NOT NULL DEFAULT 0;
ALTER TABLE news ADD COLUMN IF NOT EXISTS language VARCHAR(16) NOT NULL DEFAULT 'en';
ALTER TABLE news ADD COLUMN IF NOT EXISTS summary TEXT;
ALTER TABLE news ADD COLUMN IF NOT EXISTS translated_title VARCHAR(500);
ALTER TABLE news ADD COLUMN IF NOT EXISTS translated_content TEXT;
ALTER TABLE news ADD COLUMN IF NOT EXISTS script TEXT;
ALTER TABLE news ADD COLUMN IF NOT EXISTS tags JSON;
ALTER TABLE news ADD COLUMN IF NOT EXISTS filter_reason TEXT;
ALTER TABLE news ADD COLUMN IF NOT EXISTS raw_metadata JSON;

ALTER TABLE news ALTER COLUMN hot_score SET DEFAULT 0;
ALTER TABLE news ALTER COLUMN language SET DEFAULT 'en';

INSERT INTO news_sources (
    source_key,
    name,
    source_type,
    url,
    category,
    language,
    fetch_interval_minutes,
    is_enabled,
    extra
) VALUES
(
    'openai_blog',
    'OpenAI Blog',
    'RSS',
    'https://openai.com/blog/rss.xml',
    '模型发布',
    'en',
    360,
    TRUE,
    '{"weight": 25, "product": "openai"}'::json
),
(
    'huggingface_blog',
    'HuggingFace Blog',
    'RSS',
    'https://huggingface.co/blog/feed.xml',
    '开源生态',
    'en',
    360,
    TRUE,
    '{"weight": 20, "product": "huggingface"}'::json
)
ON CONFLICT (source_key) DO UPDATE
SET name = EXCLUDED.name,
    source_type = EXCLUDED.source_type,
    url = EXCLUDED.url,
    category = EXCLUDED.category,
    language = EXCLUDED.language,
    fetch_interval_minutes = EXCLUDED.fetch_interval_minutes,
    is_enabled = EXCLUDED.is_enabled,
    extra = EXCLUDED.extra,
    updated_at = CURRENT_TIMESTAMP;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = current_schema()
          AND table_name = 'alembic_version'
    ) THEN
        UPDATE alembic_version
        SET version_num = '20260414_0002'
        WHERE version_num IN ('20260414_0001', '20260414_0002');
    END IF;
END $$;

COMMIT;
