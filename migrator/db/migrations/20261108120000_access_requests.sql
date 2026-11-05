-- migrate:up

-- How people off the whitelist get in through the bot: off, by request (the owner approves), or paid
-- (prices and a way to pay set by the owner). Shown to them on a page in the bot.
alter table moderated_chats
    add column access_mode varchar(16) not null default 'off',
    -- The owner's own words for those who want in: rules, contacts, what the price buys
    add column access_terms text,
    -- [{"days": 30, "amount": "1000", "currency": "RUB"}], days 0: for good
    add column access_plans jsonb,
    -- link: the owner's link or requisites, the owner confirms each payment
    add column access_provider varchar(16) not null default 'link',
    add column access_payment text;

-- A request to get in: asked for free, or "I paid" by the owner's link, or (later) paid through a provider
create table access_requests (
    id bigserial primary key,
    moderated_chat_id bigint not null references moderated_chats (id) on delete cascade,
    user_service_id varchar(255) not null,
    nickname varchar(255),
    display_name varchar(255),
    language_code varchar(7),
    -- request | paid_manual | paid_auto
    kind varchar(16) not null,
    -- The plan asked for: null when the owner chooses the term, 0 for good
    days integer,
    amount numeric(12, 2),
    currency varchar(8),
    -- pending | approved | rejected
    status varchar(16) not null default 'pending',
    provider varchar(16),
    external_id varchar(255),
    decided_by varchar(255),
    decided_at timestamp,
    reminded_at timestamp,
    created_at timestamp not null,
    updated_at timestamp not null
);

-- One open request per member and group
create unique index access_requests_pending_key
    on access_requests (moderated_chat_id, user_service_id) where status = 'pending';
create unique index access_requests_provider_external_id_key
    on access_requests (provider, external_id) where external_id is not null;


-- migrate:down

drop table access_requests;

alter table moderated_chats
    drop column access_payment,
    drop column access_provider,
    drop column access_plans,
    drop column access_terms,
    drop column access_mode;
