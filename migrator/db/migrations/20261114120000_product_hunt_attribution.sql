-- migrate:up
-- Existing rows intentionally remain NULL: their historical acquisition source is unknown.
ALTER TABLE users ADD COLUMN first_source varchar(32);

CREATE TABLE attribution_events (
    id bigserial PRIMARY KEY,
    event_key varchar(255) NOT NULL UNIQUE,
    event_type varchar(40) NOT NULL,
    occurred_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    user_id bigint NOT NULL REFERENCES users(id),
    touch_source varchar(32),
    is_new_user boolean,
    -- Keep the historical group id when a link or group row is later deleted.
    moderated_chat_id bigint,
    owner boolean,
    amount_minor bigint,
    currency_code varchar(3),
    details jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX attribution_events_type_time_idx ON attribution_events (event_type, occurred_at);
CREATE INDEX attribution_events_user_time_idx ON attribution_events (user_id, occurred_at);

COMMENT ON TABLE attribution_events IS
    'Product Hunt attribution detail; the hourly subscription task deletes rows older than 12 months.';

-- migrate:down
DROP TABLE attribution_events;
ALTER TABLE users DROP COLUMN first_source;
