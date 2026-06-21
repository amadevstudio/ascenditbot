-- migrate:up

create table currencies(
    code varchar(16) primary key not null,
    title varchar(255) not null,
    minor_units smallint not null default 2,
    payment_provider varchar(255),
    enabled boolean not null default true,
    created_at timestamp not null,
    updated_at timestamp not null
);

insert into currencies (code, title, minor_units, payment_provider, enabled, created_at, updated_at) values
('rub', 'RUB', 2, 'robokassa.ru', true, now(), now()),
('usd', 'USD', 2, 'robokassa.ru', true, now(), now());

alter table tariff_prices
alter column currency_code type varchar(16);

alter table payments_history
alter column currency_code type varchar(16);

insert into currencies (code, title, minor_units, payment_provider, enabled, created_at, updated_at)
select currency_code, upper(currency_code), 2, null, false, now(), now()
from (
    select currency_code from tariff_prices where currency_code is not null
    union
    select currency_code from payments_history where currency_code is not null
    union
    select currency_code from user_tariff_connections where currency_code is not null
) as existing_currencies
where currency_code not in (select code from currencies)
on conflict (code) do nothing;

insert into tariff_prices (tariff_id, currency_code, price, created_at, updated_at) values
(0, 'rub', 0, now(), now()),
(0, 'usd', 0, now(), now())
on conflict (tariff_id, currency_code) do nothing;

delete from tariff_prices
where tariff_id = 0 and currency_code is null;

alter table tariff_prices
add constraint fk_currency foreign key(currency_code) references currencies(code);

alter table payments_history
add constraint fk_currency foreign key(currency_code) references currencies(code);

create table user_balances(
    user_id bigint not null,
    currency_code varchar(16) not null,
    balance integer not null default 0,
    created_at timestamp not null,
    updated_at timestamp not null,
    constraint fk_user foreign key(user_id) references users(id),
    constraint fk_currency foreign key(currency_code) references currencies(code),
    unique (user_id, currency_code)
);

alter table user_tariff_connections
add column payment_currency_code varchar(16);

update user_tariff_connections
set payment_currency_code = currency_code;

update user_tariff_connections
set payment_currency_code = 'usd'
where payment_currency_code not in (
    select code from currencies where enabled is true
);

insert into user_balances (user_id, currency_code, balance, created_at, updated_at)
select user_id, payment_currency_code, balance, now(), now()
from user_tariff_connections
on conflict (user_id, currency_code) do update
set balance = user_balances.balance + excluded.balance,
    updated_at = now();

insert into user_balances (user_id, currency_code, balance, created_at, updated_at)
select u.id, c.code, 0, now(), now()
from users as u
cross join currencies as c
where c.enabled is true
on conflict (user_id, currency_code) do nothing;

alter table user_tariff_connections
alter column payment_currency_code set not null;

alter table user_tariff_connections
add constraint fk_payment_currency foreign key(payment_currency_code) references currencies(code);

alter table user_tariff_connections
drop column balance,
drop column currency_code;

-- migrate:down

alter table user_tariff_connections
add column balance integer not null default 0,
add column currency_code varchar(3);

update user_tariff_connections as utc
set currency_code = utc.payment_currency_code,
    balance = coalesce(ub.balance, 0)
from user_balances as ub
where ub.user_id = utc.user_id
    and ub.currency_code = utc.payment_currency_code;

alter table user_tariff_connections
alter column currency_code set not null;

alter table user_tariff_connections
drop constraint fk_payment_currency,
drop column payment_currency_code;

drop table user_balances;

alter table payments_history
drop constraint fk_currency;

alter table tariff_prices
drop constraint fk_currency;

delete from tariff_prices
where tariff_id = 0 and currency_code in ('rub', 'usd');

insert into tariff_prices (tariff_id, currency_code, price, created_at, updated_at) values
(0, Null, 0, now(), now())
on conflict (tariff_id, currency_code) do nothing;

alter table tariff_prices
alter column currency_code type varchar(3);

alter table payments_history
alter column currency_code type varchar(3);

drop table currencies;
