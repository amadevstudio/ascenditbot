-- migrate:up
create table users (
    id bigserial primary key not null,
    service_id varchar(255) not null,
    language_code varchar(7),
    ref_id bigint,
    created_at timestamp not null,
    updated_at timestamp not null
);
create index "service_id_index_on_users" on "users" ("service_id");

create table moderated_chats (
    id bigserial primary key not null,
    service_id varchar(255) not null,
    active boolean not null default true,
    disabled boolean not null default false,
    allow_administrators boolean not null default true,
    allowed_keywords varchar(255)[],
    created_at timestamp not null,
    updated_at timestamp not null
);
create index "service_id_index_on_moderated_chats" on "moderated_chats" ("service_id");

create table user_moderated_chat_connections (
    id bigserial primary key not null,
    user_id bigint not null,
    owner boolean not null default false,
    moderated_chat_id bigint not null,
    created_at timestamp not null,
    updated_at timestamp not null,
--    primary key (user_id, moderated_chat_id),
    constraint fk_user foreign key(user_id) references users(id),
    constraint fk_moderated_chat foreign key(moderated_chat_id) references moderated_chats(id),
    unique (user_id, moderated_chat_id)
);

create table allowed_users (
    id bigserial primary key not null,
    moderated_chat_id bigint not null,
    nickname varchar(255),
--    service_id varchar(255),
    active boolean not null default true,
    images_allowed boolean not null default true,
    links_allowed boolean not null default true,
    period_quantity integer,
    period_type varchar(255),
    period_quantity_left integer,
    ban_expiration_date timestamp,
    created_at timestamp not null,
    updated_at timestamp not null,
    constraint fk_moderated_chat foreign key(moderated_chat_id) references moderated_chats(id),
    unique (moderated_chat_id, nickname)
);

create table moderated_chat_statistics (
    id bigserial primary key not null,
    moderated_chat_id bigint not null,
    deleted_messages_count bigint default 0,
    created_at timestamp not null,
    updated_at timestamp not null,
    constraint fk_moderated_chat foreign key(moderated_chat_id) references moderated_chats(id)
);

-- migrate:down

drop table moderated_chat_statistics;
drop table allowed_users;
drop table user_moderated_chat_connections;
drop table moderated_chats;
drop table users;

