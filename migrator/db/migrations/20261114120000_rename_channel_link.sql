-- migrate:up

-- The channel was renamed from @ascendit_group to @ascendit_channel: the old t.me link no longer opens it
update promo_channels set link = replace(link, 't.me/ascendit_group', 't.me/ascendit_channel'), updated_at = current_timestamp
where link like '%t.me/ascendit_group%';

-- migrate:down

update promo_channels set link = replace(link, 't.me/ascendit_channel', 't.me/ascendit_group'), updated_at = current_timestamp
where link like '%t.me/ascendit_channel%';
