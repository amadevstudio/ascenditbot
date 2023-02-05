-- migrate:up

alter table users
add column email varchar(255) UNIQUE;

-- migrate:down

alter table users
drop column email;
