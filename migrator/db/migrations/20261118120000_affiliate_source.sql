-- migrate:up

-- The links of Telegram's affiliate program (t.me/<bot>?start=_tgr_<code>, made by Telegram for each affiliate):
-- one source for all of them, so the people they bring show up in the reports
insert into attribution_sources (tag) values ('affiliate') on conflict (tag) do nothing;


-- migrate:down

delete from attribution_sources where tag = 'affiliate';
