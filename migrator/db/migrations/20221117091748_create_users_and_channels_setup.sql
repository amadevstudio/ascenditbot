-- migrate:up
create table users (
    id bigserial primary key not null,
    service_id varchar(255) not null,
    language_code varchar(7),
    ref_id bigint,
    created_at timestamp not null,
    updated_at timestamp not null
);
create index "service_id_index" on "users" ("service_id");

create table moderated_groups (
    id bigserial primary key not null,
    active boolean not null default true,
    disabled boolean not null default false,
    allow_administrators boolean not null default true,
    allowed_keywords varchar(255)[],
    created_at timestamp not null,
    updated_at timestamp not null
);

create table user_moderated_groups_connections (
    user_id bigint not null,
    moderated_group_id bigint not null,
    created_at timestamp not null,
    updated_at timestamp not null,
    primary key (user_id, moderated_group_id),
    constraint fk_user foreign key(user_id) references users(id),
    constraint fk_moderated_group foreign key(moderated_group_id) references moderated_groups(id)
);

create table allowed_users (
    id bigserial primary key not null,
    moderated_group_id bigint not null,
    nickname varchar(255),
    service_id varchar(255),
    active boolean not null,
    images_allowed boolean not null,
    links_allowed boolean not null,
    period_quantity integer,
    period_type varchar(255),
    period_quantity_left integer,
    ban_expiration_date timestamp,
    created_at timestamp not null,
    updated_at timestamp not null,
    constraint fk_moderated_group foreign key(moderated_group_id) references moderated_groups(id)
);

create table moderated_group_statistics (
    id bigserial primary key not null,
    moderated_group_id bigint not null,
    deleted_messages_count bigint default 0,
    created_at timestamp not null,
    updated_at timestamp not null,
    constraint fk_moderated_group foreign key(moderated_group_id) references moderated_groups(id)
);

-- migrate:down

drop table moderated_group_statistics;
drop table allowed_users;
drop table user_moderated_groups_connections;
drop table moderated_groups;
drop table users;

