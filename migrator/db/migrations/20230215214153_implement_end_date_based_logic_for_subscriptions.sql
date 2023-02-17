-- migrate:up

alter table user_tariff_connections
rename column start_date to end_date;

alter table user_tariff_connections
add column trial_was_activated bool not null default false;

update user_tariff_connections set end_date = end_date + interval '30 day', trial_was_activated = true;

-- migrate:down

alter table user_tariff_connections
rename column end_date to start_date;

update user_tariff_connections set start_date = start_date - interval '30 day';

alter table user_tariff_connections
drop column trial_was_activated;
