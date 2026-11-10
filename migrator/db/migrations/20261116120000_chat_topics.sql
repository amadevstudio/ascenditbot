-- migrate:up

-- The topics of a group with topics, as the bot has seen them in messages (Telegram gives bots no list of topics).
-- protected: the group's rules apply in the topic; not protected: the bot leaves the topic alone.
-- thread_id 1 is the general topic.
create table chat_topics (
    moderated_chat_id bigint not null references moderated_chats (id) on delete cascade,
    thread_id bigint not null,
    name varchar(255),
    protected boolean not null,
    closed boolean not null default false,
    seen_at timestamp not null default LOCALTIMESTAMP,
    created_at timestamp not null default LOCALTIMESTAMP,
    primary key (moderated_chat_id, thread_id)
);

-- Whether a topic the bot sees for the first time is protected
alter table moderated_chats add column topics_default_protected boolean not null default true;

-- migrate:down

alter table moderated_chats drop column topics_default_protected;
drop table chat_topics;
