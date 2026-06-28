-- migrate:up

alter table moderated_chats
add column restriction_duration_minutes integer not null default 5;


-- migrate:down

alter table moderated_chats
drop column restriction_duration_minutes;
