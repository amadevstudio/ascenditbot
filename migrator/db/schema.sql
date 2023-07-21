SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: allowed_users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.allowed_users (
    id bigint NOT NULL,
    moderated_chat_id bigint NOT NULL,
    nickname character varying(255),
    active boolean DEFAULT true NOT NULL,
    images_allowed boolean DEFAULT true NOT NULL,
    links_allowed boolean DEFAULT true NOT NULL,
    period_quantity integer,
    period_type character varying(255),
    period_quantity_left integer,
    ban_expiration_date timestamp without time zone,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


--
-- Name: allowed_users_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.allowed_users_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: allowed_users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.allowed_users_id_seq OWNED BY public.allowed_users.id;


--
-- Name: lang_country_curr_codes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.lang_country_curr_codes (
    language_code character varying(3) NOT NULL,
    country_code character varying(3) NOT NULL,
    currency_code character varying(3) NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


--
-- Name: moderated_chat_statistics; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.moderated_chat_statistics (
    id bigint NOT NULL,
    moderated_chat_id bigint NOT NULL,
    deleted_messages_count bigint DEFAULT 0,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


--
-- Name: moderated_chat_statistics_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.moderated_chat_statistics_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: moderated_chat_statistics_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.moderated_chat_statistics_id_seq OWNED BY public.moderated_chat_statistics.id;


--
-- Name: moderated_chats; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.moderated_chats (
    id bigint NOT NULL,
    service_id character varying(255) NOT NULL,
    active boolean DEFAULT true NOT NULL,
    disabled boolean DEFAULT false NOT NULL,
    allow_administrators boolean DEFAULT true NOT NULL,
    allowed_keywords character varying(255)[],
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    name character varying(255)
);


--
-- Name: moderated_chats_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.moderated_chats_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: moderated_chats_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.moderated_chats_id_seq OWNED BY public.moderated_chats.id;


--
-- Name: payments_history; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.payments_history (
    id bigint NOT NULL,
    user_id bigint NOT NULL,
    payment_service character varying(255) NOT NULL,
    status smallint DEFAULT 0 NOT NULL,
    amount integer DEFAULT 0 NOT NULL,
    currency_code character varying(3) NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


--
-- Name: payments_history_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.payments_history_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: payments_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.payments_history_id_seq OWNED BY public.payments_history.id;


--
-- Name: schema_migrations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.schema_migrations (
    version character varying(255) NOT NULL
);


--
-- Name: tariff_prices; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tariff_prices (
    tariff_id bigint NOT NULL,
    currency_code character varying(3),
    price integer NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


--
-- Name: tariffs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tariffs (
    id bigint NOT NULL,
    channels_count smallint,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


--
-- Name: tariffs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tariffs_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: tariffs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.tariffs_id_seq OWNED BY public.tariffs.id;


--
-- Name: user_moderated_chat_connections; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_moderated_chat_connections (
    id bigint NOT NULL,
    user_id bigint NOT NULL,
    owner boolean DEFAULT false NOT NULL,
    moderated_chat_id bigint NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


--
-- Name: user_moderated_chat_connections_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.user_moderated_chat_connections_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: user_moderated_chat_connections_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.user_moderated_chat_connections_id_seq OWNED BY public.user_moderated_chat_connections.id;


--
-- Name: user_tariff_connections; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_tariff_connections (
    user_id bigint NOT NULL,
    tariff_id bigint NOT NULL,
    balance integer DEFAULT 0 NOT NULL,
    currency_code character varying(3) NOT NULL,
    end_date timestamp without time zone,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    trial_was_activated boolean DEFAULT false NOT NULL
);


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    id bigint NOT NULL,
    service_id character varying(255) NOT NULL,
    language_code character varying(7),
    ref_id bigint,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    email character varying(255),
    nickname character varying(255),
    is_admin boolean DEFAULT false NOT NULL
);


--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.users_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: allowed_users id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.allowed_users ALTER COLUMN id SET DEFAULT nextval('public.allowed_users_id_seq'::regclass);


--
-- Name: moderated_chat_statistics id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moderated_chat_statistics ALTER COLUMN id SET DEFAULT nextval('public.moderated_chat_statistics_id_seq'::regclass);


--
-- Name: moderated_chats id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moderated_chats ALTER COLUMN id SET DEFAULT nextval('public.moderated_chats_id_seq'::regclass);


--
-- Name: payments_history id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payments_history ALTER COLUMN id SET DEFAULT nextval('public.payments_history_id_seq'::regclass);


--
-- Name: tariffs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tariffs ALTER COLUMN id SET DEFAULT nextval('public.tariffs_id_seq'::regclass);


--
-- Name: user_moderated_chat_connections id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_moderated_chat_connections ALTER COLUMN id SET DEFAULT nextval('public.user_moderated_chat_connections_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Name: allowed_users allowed_users_moderated_chat_id_nickname_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.allowed_users
    ADD CONSTRAINT allowed_users_moderated_chat_id_nickname_key UNIQUE (moderated_chat_id, nickname);


--
-- Name: allowed_users allowed_users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.allowed_users
    ADD CONSTRAINT allowed_users_pkey PRIMARY KEY (id);


--
-- Name: lang_country_curr_codes lang_country_curr_codes_language_code_country_code_currency_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lang_country_curr_codes
    ADD CONSTRAINT lang_country_curr_codes_language_code_country_code_currency_key UNIQUE (language_code, country_code, currency_code);


--
-- Name: moderated_chat_statistics moderated_chat_statistics_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moderated_chat_statistics
    ADD CONSTRAINT moderated_chat_statistics_pkey PRIMARY KEY (id);


--
-- Name: moderated_chats moderated_chats_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moderated_chats
    ADD CONSTRAINT moderated_chats_pkey PRIMARY KEY (id);


--
-- Name: payments_history payments_history_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payments_history
    ADD CONSTRAINT payments_history_pkey PRIMARY KEY (id);


--
-- Name: schema_migrations schema_migrations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.schema_migrations
    ADD CONSTRAINT schema_migrations_pkey PRIMARY KEY (version);


--
-- Name: tariff_prices tariff_prices_tariff_id_currency_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tariff_prices
    ADD CONSTRAINT tariff_prices_tariff_id_currency_code_key UNIQUE (tariff_id, currency_code);


--
-- Name: tariffs tariffs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tariffs
    ADD CONSTRAINT tariffs_pkey PRIMARY KEY (id);


--
-- Name: user_moderated_chat_connections user_moderated_chat_connections_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_moderated_chat_connections
    ADD CONSTRAINT user_moderated_chat_connections_pkey PRIMARY KEY (id);


--
-- Name: user_moderated_chat_connections user_moderated_chat_connections_user_id_moderated_chat_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_moderated_chat_connections
    ADD CONSTRAINT user_moderated_chat_connections_user_id_moderated_chat_id_key UNIQUE (user_id, moderated_chat_id);


--
-- Name: user_tariff_connections user_tariff_connections_user_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_tariff_connections
    ADD CONSTRAINT user_tariff_connections_user_id_key UNIQUE (user_id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: service_id_index_on_moderated_chats; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX service_id_index_on_moderated_chats ON public.moderated_chats USING btree (service_id);


--
-- Name: service_id_index_on_users; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX service_id_index_on_users ON public.users USING btree (service_id);


--
-- Name: user_moderated_chat_connections fk_moderated_chat; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_moderated_chat_connections
    ADD CONSTRAINT fk_moderated_chat FOREIGN KEY (moderated_chat_id) REFERENCES public.moderated_chats(id);


--
-- Name: allowed_users fk_moderated_chat; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.allowed_users
    ADD CONSTRAINT fk_moderated_chat FOREIGN KEY (moderated_chat_id) REFERENCES public.moderated_chats(id);


--
-- Name: moderated_chat_statistics fk_moderated_chat; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.moderated_chat_statistics
    ADD CONSTRAINT fk_moderated_chat FOREIGN KEY (moderated_chat_id) REFERENCES public.moderated_chats(id);


--
-- Name: tariff_prices fk_tariff; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tariff_prices
    ADD CONSTRAINT fk_tariff FOREIGN KEY (tariff_id) REFERENCES public.tariffs(id);


--
-- Name: user_tariff_connections fk_tariff; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_tariff_connections
    ADD CONSTRAINT fk_tariff FOREIGN KEY (tariff_id) REFERENCES public.tariffs(id);


--
-- Name: user_moderated_chat_connections fk_user; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_moderated_chat_connections
    ADD CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: user_tariff_connections fk_user; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_tariff_connections
    ADD CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: payments_history fk_user; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payments_history
    ADD CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- PostgreSQL database dump complete
--


--
-- Dbmate schema migrations
--

INSERT INTO public.schema_migrations (version) VALUES
    ('20221117091748'),
    ('20230101203133'),
    ('20230205105440'),
    ('20230215214153'),
    ('20230217162034'),
    ('20230317222504');
