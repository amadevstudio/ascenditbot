-- migrate:up

-- Looking through the group's history for topics by id (MTProto messages.getForumTopicsByID): the ids up to
-- topics_scanned_to are looked at, topics_scan_upper is the newest message id known, topics_scanned_at when the
-- look reached it last
alter table moderated_chats add column topics_scanned_to bigint not null default 1;
alter table moderated_chats add column topics_scan_upper bigint;
alter table moderated_chats add column topics_scanned_at timestamp;

-- migrate:down

alter table moderated_chats drop column topics_scanned_at;
alter table moderated_chats drop column topics_scan_upper;
alter table moderated_chats drop column topics_scanned_to;
