-- migrate:up

insert into currencies (code, title, minor_units, payment_provider, enabled, created_at, updated_at) values
('xtr', 'Telegram Stars', 0, 'telegram_stars', true, now(), now())
on conflict (code) do update
set title = excluded.title,
    minor_units = excluded.minor_units,
    payment_provider = excluded.payment_provider,
    enabled = excluded.enabled,
    updated_at = now();

insert into tariff_prices (tariff_id, currency_code, price, created_at, updated_at) values
(0, 'xtr', 0, now(), now()),
(1, 'xtr', 350, now(), now()),
(2, 'xtr', 1100, now(), now()),
(3, 'xtr', 3500, now(), now())
on conflict (tariff_id, currency_code) do update
set price = excluded.price,
    updated_at = now();

insert into user_balances (user_id, currency_code, balance, created_at, updated_at)
select u.id, 'xtr', 0, now(), now()
from users as u
on conflict (user_id, currency_code) do nothing;

alter table payments_history
add column external_payment_id varchar(255),
add column invoice_payload varchar(255);

alter table payments_history
add constraint payments_history_payment_service_external_payment_id_key
unique (payment_service, external_payment_id);

-- migrate:down

alter table payments_history
drop constraint payments_history_payment_service_external_payment_id_key,
drop column invoice_payload,
drop column external_payment_id;

delete from user_balances
where currency_code = 'xtr';

delete from tariff_prices
where currency_code = 'xtr';

delete from currencies
where code = 'xtr';
