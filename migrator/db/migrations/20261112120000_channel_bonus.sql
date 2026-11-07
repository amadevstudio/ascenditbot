-- migrate:up

-- Channels whose subscribers get bonus days of the paid tariff; the bot's owner manages them with /admin
create table promo_channels (
    id bigserial primary key,
    service_id varchar(255) not null unique,
    title varchar(255),
    link varchar(255),
    created_at timestamp not null default current_timestamp,
    updated_at timestamp not null default current_timestamp
);

-- Who took the bonus, for which channels, and since when they are not subscribed any more: then their free group
-- waits until they subscribe again
create table channel_bonus_claims (
    user_id bigint primary key references users (id) on delete cascade,
    channel_ids varchar(255)[] not null,
    claimed_at timestamp not null default current_timestamp,
    lost_at timestamp,
    checked_at timestamp not null default current_timestamp
);


-- migrate:down

drop table channel_bonus_claims;
drop table promo_channels;
