-- migrate:up

create table tariffs(
    id bigserial primary key not null,
    channels_count smallint,
    created_at timestamp not null,
    updated_at timestamp not null
);

create table tariff_prices(
    tariff_id bigint not null,
    currency_code varchar(3) not null,
    price integer not null,
    created_at timestamp not null,
    updated_at timestamp not null,
    constraint fk_tariff foreign key(tariff_id) references tariffs(id),
    unique (tariff_id, currency_code)
);

create table lang_country_curr_codes(
    language_code varchar(3) not null,
    country_code varchar(3) not null,
    currency_code varchar(3) not null,
    created_at timestamp not null,
    updated_at timestamp not null,
    unique (language_code, country_code, currency_code)
);

create table user_tariff_connections(
    user_id bigint not null,
    tariff_id bigint not null,
    balance integer not null default 0,
    currency_code varchar(3) not null,
    start_date timestamp not null,
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
    amount integer not null default 0,
    currency_code varchar(3) not null,
    created_at timestamp not null,
    updated_at timestamp not null,
    constraint fk_user foreign key(user_id) references users(id)
);

-- migrate:down

drop table payments_history;
drop table user_tariff_connections;
drop table lang_country_curr_codes;
drop table tariff_prices;
drop table tariffs;
