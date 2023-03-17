-- migrate:up

alter table users
add column is_admin boolean not null default false;

-- migrate:down

alter table users
drop column is_admin;
