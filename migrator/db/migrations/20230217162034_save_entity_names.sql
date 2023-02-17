-- migrate:up

alter table moderated_chats
add column name varchar(255);

alter table users
add column nickname varchar(255);


-- migrate:down

alter table moderated_chats
drop column name;

alter table users
drop column nickname;

