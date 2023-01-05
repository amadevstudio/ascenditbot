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

insert into tariffs (id, channels_count, created_at, updated_at) values
(1, 1, now(), now()),
(2, 10, now(), now()),
(3, null, now(), now());

insert into tariff_prices (tariff_id, currency_code, price, created_at, updated_at) values
(1, 'rub', 30000, now(), now()),
(1, 'usd', 450, now(), now()),
(2, 'rub', 100000, now(), now()),
(2, 'usd', 1400, now(), now()),
(3, 'rub', 300000, now(), now()),
(3, 'usd', 4500, now(), now());

insert into lang_country_curr_codes (language_code, country_code, currency_code, created_at, updated_at) values
('ru', 'rus', 'rub', now(), now()),
('en', 'usa', 'usd', now(), now());

--insert into user_tariff_connections (user_id, tariff_id, balance, currency_code, start_date, created_at, updated_at)
--values (1, 1, 500000, 'rub', '2023-01-05 12:30:00', now(), now());

-- migrate:down

drop table payments_history;
drop table user_tariff_connections;
drop table lang_country_curr_codes;
drop table tariff_prices;
drop table tariffs;
