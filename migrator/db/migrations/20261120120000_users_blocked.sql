-- migrate:up

-- When the user blocked the bot (my_chat_member in the private chat, status kicked); null while the bot can write
-- to them. The admin numbers count the people the bot can still reach.
alter table users add column blocked_at timestamp;


-- migrate:down

alter table users drop column blocked_at;
