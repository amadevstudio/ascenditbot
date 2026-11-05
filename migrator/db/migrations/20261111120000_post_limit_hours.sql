-- migrate:up

-- A posting limit is "n posts in any m hours" now, not per calendar day or week
alter table moderated_chats add column post_limit_hours smallint;
update moderated_chats
set post_limit_hours = case post_limit_period when 'week' then 168 else 24 end
where post_limit is not null;
alter table moderated_chats drop column post_limit_period;

-- migrate:down

alter table moderated_chats add column post_limit_period varchar(8);
update moderated_chats
set post_limit_period = case when post_limit_hours >= 168 then 'week' else 'day' end
where post_limit is not null;
alter table moderated_chats drop column post_limit_hours;
