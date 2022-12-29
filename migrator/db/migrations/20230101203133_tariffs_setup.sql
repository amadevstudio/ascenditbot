-- migrate:up

create table tariffs(
    id bigserial primary key not null,
    price integer not null,
    channels_count smallint,
    created_at timestamp not null,
    updated_at timestamp not null
);

create table user_tariff_connections(
    user_id bigint not null,
    tariff_id bigint not null,
    balance integer not null default 0,
    start_data timestamp not null,
    created_at timestamp not null,
    updated_at timestamp not null,
    constraint fk_user foreign key(user_id) references users(id),
    constraint fk_tariff foreign key(tariff_id) references tariffs(id),
    unique (user_id, tariff_id)
);

create table payments_history(
    id bigserial primary key not null,
    user_id bigint not null,
    payment_service varchar(255) not null,
    status smallint not null default 0,
    created_at timestamp not null,
    updated_at timestamp not null,
    constraint fk_user foreign key(user_id) references users(id)
);

-- migrate:down

drop table payments_history;
drop table user_tariff_connections;
drop table tariffs;
