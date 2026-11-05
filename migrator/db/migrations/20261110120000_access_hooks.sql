-- migrate:up

-- Providers that tell the bot about a payment (YooMoney, Tribute) call https://.../hook/<provider>/<key>: the key
-- comes from the owner's wallet or API key, so one wallet used by several groups has one address
alter table moderated_chats add column access_hook_key varchar(64);
create index moderated_chats_access_hook_key_index on moderated_chats (access_hook_key)
    where access_hook_key is not null;


-- migrate:down

drop index moderated_chats_access_hook_key_index;
alter table moderated_chats drop column access_hook_key;
