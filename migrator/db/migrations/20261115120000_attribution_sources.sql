-- migrate:up

-- The tags of t.me/<bot>?start=src_<tag> links the bot's owner made in /admin: a /start with another tag is no
-- source, so a made-up link does not show up in the reports
create table attribution_sources (
    tag varchar(32) primary key,
    created_at timestamp not null default current_timestamp
);

-- The Product Hunt link has been out since 20261114120000_product_hunt_attribution
insert into attribution_sources (tag) values ('ph2');


-- migrate:down

drop table attribution_sources;
