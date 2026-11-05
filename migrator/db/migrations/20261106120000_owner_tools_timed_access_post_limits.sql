-- migrate:up

-- Whitelist entries by Telegram user id as well as by nickname: people without a username can be allowed,
-- and a renamed member keeps access. An entry can also run out (timed access, a paid feature).
alter table allowed_users
    add column user_service_id varchar(255),
    -- First and last name, for people without a username
    add column display_name varchar(255),
    add column expires_at timestamp,
    -- 0: nothing sent, 1: the owner was reminded a day before, 2: the owner was told it ran out
    add column expiry_notice smallint not null default 0;

create unique index allowed_users_moderated_chat_id_user_service_id_key
    on allowed_users (moderated_chat_id, user_service_id) where user_service_id is not null;

-- Per group: who may write (the whitelist or everyone), a posting limit per member, the owner's alerts
alter table moderated_chats
    add column everyone_can_write boolean not null default false,
    add column post_limit smallint,
    add column post_limit_period varchar(8),
    add column owner_alerts boolean not null default true;

-- Removed messages per group and day (the table existed unused)
alter table moderated_chat_statistics add column day date not null default current_date;
-- Old rows, if any, all fall on today: keep one per group so that the index can be built
delete from moderated_chat_statistics as a
    using moderated_chat_statistics as b
    where a.moderated_chat_id = b.moderated_chat_id and a.id > b.id;
create unique index moderated_chat_statistics_moderated_chat_id_day_key
    on moderated_chat_statistics (moderated_chat_id, day);

-- The cheapest paid tariff moderated one group, as many as the free one: now three
update tariffs set channels_count = 3, updated_at = current_timestamp where id = 1;


-- migrate:down

update tariffs set channels_count = 1, updated_at = current_timestamp where id = 1;

drop index moderated_chat_statistics_moderated_chat_id_day_key;
alter table moderated_chat_statistics drop column day;

alter table moderated_chats
    drop column owner_alerts,
    drop column post_limit_period,
    drop column post_limit,
    drop column everyone_can_write;

drop index allowed_users_moderated_chat_id_user_service_id_key;
alter table allowed_users
    drop column expiry_notice,
    drop column expires_at,
    drop column display_name,
    drop column user_service_id;
