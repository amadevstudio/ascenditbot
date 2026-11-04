-- migrate:up

-- The free tariff (id 0) now moderates one chat instead of none
update tariffs set channels_count = 1, updated_at = current_timestamp where id = 0;

-- Free users get their first chat back (the same one update_user_moderated_chats keeps: the oldest owner
-- connection), but paused: these chats lived without moderation for a while, so the owner turns it on
update moderated_chats as mc
set disabled = false, active = false, updated_at = current_timestamp
where mc.id in (
    select distinct on (umcc.user_id) umcc.moderated_chat_id
    from user_moderated_chat_connections as umcc
        inner join user_tariff_connections as utc on (utc.user_id = umcc.user_id and utc.tariff_id = 0)
    where umcc.owner is true
    order by umcc.user_id, umcc.id asc
)
and mc.disabled is true;


-- migrate:down

update tariffs set channels_count = 0, updated_at = current_timestamp where id = 0;

update moderated_chats as mc
set disabled = true, updated_at = current_timestamp
from user_moderated_chat_connections as umcc
    inner join user_tariff_connections as utc on (utc.user_id = umcc.user_id and utc.tariff_id = 0)
where umcc.moderated_chat_id = mc.id and umcc.owner is true;
