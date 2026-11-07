-- migrate:up

-- The channels a bonus taker has left and lost days for: once per channel, subscribing again gives nothing back
alter table channel_bonus_claims add column penalized_channel_ids varchar(255)[] not null default '{}';

-- migrate:down

alter table channel_bonus_claims drop column penalized_channel_ids;
