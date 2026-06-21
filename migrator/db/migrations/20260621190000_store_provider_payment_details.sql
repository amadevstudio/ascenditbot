-- migrate:up

alter table payments_history
add column provider_out_sum varchar(64),
add column provider_inc_sum varchar(64),
add column provider_inc_curr_label varchar(255),
add column provider_payment_method varchar(255);

-- migrate:down

alter table payments_history
drop column provider_payment_method,
drop column provider_inc_curr_label,
drop column provider_inc_sum,
drop column provider_out_sum;
