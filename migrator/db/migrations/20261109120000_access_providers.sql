-- migrate:up

-- Payment through a provider that confirms it (CryptoBot): the owner's credentials, encrypted by the bot, and
-- what to show about them (the app's name)
alter table moderated_chats
    add column access_secret text,
    add column access_provider_label varchar(255);

-- The provider's payment page of a request, while it waits to be paid
alter table access_requests add column pay_url text;


-- migrate:down

alter table access_requests drop column pay_url;

alter table moderated_chats
    drop column access_provider_label,
    drop column access_secret;
