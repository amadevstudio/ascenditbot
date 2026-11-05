-- migrate:up

-- Tariff 1 now covers 3 groups, as many as tariff 2 did: each step up covers clearly more, and a group costs
-- less the more of them are paid for (300, 750, 1500 rub for 3, 10, 25 groups)
update tariffs set channels_count = 10, updated_at = current_timestamp where id = 2;
update tariffs set channels_count = 25, updated_at = current_timestamp where id = 3;


-- migrate:down

update tariffs set channels_count = 8, updated_at = current_timestamp where id = 3;
update tariffs set channels_count = 3, updated_at = current_timestamp where id = 2;
