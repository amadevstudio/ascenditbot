-- migrate:up

alter table user_tariff_connections
rename column start_date to end_date;

-- migrate:down

alter table user_tariff_connections
rename column end_date to start_date;
