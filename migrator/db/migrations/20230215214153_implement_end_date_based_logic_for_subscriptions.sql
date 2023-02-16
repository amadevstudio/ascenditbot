-- migrate:up

alter table user_tariff_connections
rename column start_date to end_date;

update user_tariff_connections set end_date = end_date + interval '30 day';

-- migrate:down

alter table user_tariff_connections
rename column end_date to start_date;

update user_tariff_connections set start_date = start_date - interval '30 day';
