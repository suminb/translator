--
-- PostgreSQL database dump
--

SET statement_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = off;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET escape_string_warning = off;

SET search_path = public, pg_catalog;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: rating; Type: TABLE; Schema: public; Owner: sumin_translator; Tablespace: 
--

CREATE TABLE rating (
    id uuid NOT NULL,
    translation_id uuid NOT NULL,
    "timestamp" timestamp with time zone NOT NULL,
    user_agent character varying(255),
    remote_address character varying(64),
    rating smallint NOT NULL,
    token character varying(128)
);


ALTER TABLE public.rating OWNER TO sumin_translator;

--
-- Name: COLUMN rating.rating; Type: COMMENT; Schema: public; Owner: sumin_translator
--

COMMENT ON COLUMN rating.rating IS '-1, 0, +1';


--
-- Name: translation; Type: TABLE; Schema: public; Owner: sumin_translator; Tablespace: 
--

CREATE TABLE translation (
    id uuid NOT NULL,
    serial integer,
    "timestamp" timestamp with time zone NOT NULL,
    user_agent character varying(255),
    remote_address character varying(64),
    source character varying(16) NOT NULL,
    target character varying(16) NOT NULL,
    mode smallint NOT NULL,
    original_text text NOT NULL,
    translated_text text,
    intermediate_text text,
    original_text_hash character varying(255)
);


ALTER TABLE public.translation OWNER TO sumin_translator;

--
-- Name: COLUMN translation.original_text_hash; Type: COMMENT; Schema: public; Owner: sumin_translator
--

COMMENT ON COLUMN translation.original_text_hash IS 'Locality Sensitive Hash (LSH) value of original_text';


--
-- Name: translation_serial_seq; Type: SEQUENCE; Schema: public; Owner: sumin_translator
--

CREATE SEQUENCE translation_serial_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.translation_serial_seq OWNER TO sumin_translator;

--
-- Name: translation_serial_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: sumin_translator
--

ALTER SEQUENCE translation_serial_seq OWNED BY translation.serial;


--
-- Name: serial; Type: DEFAULT; Schema: public; Owner: sumin_translator
--

ALTER TABLE ONLY translation ALTER COLUMN serial SET DEFAULT nextval('translation_serial_seq'::regclass);


--
-- Name: rating_pkey; Type: CONSTRAINT; Schema: public; Owner: sumin_translator; Tablespace: 
--

ALTER TABLE ONLY rating
    ADD CONSTRAINT rating_pkey PRIMARY KEY (id);


--
-- Name: translation_pkey; Type: CONSTRAINT; Schema: public; Owner: sumin_translator; Tablespace: 
--

ALTER TABLE ONLY translation
    ADD CONSTRAINT translation_pkey PRIMARY KEY (id);


--
-- Name: original_text_hash; Type: INDEX; Schema: public; Owner: sumin_translator; Tablespace: 
--

CREATE INDEX original_text_hash ON translation USING btree (original_text_hash);


--
-- Name: serial; Type: INDEX; Schema: public; Owner: sumin_translator; Tablespace: 
--

CREATE UNIQUE INDEX serial ON translation USING btree (serial);

ALTER TABLE translation CLUSTER ON serial;


--
-- Name: translation; Type: FK CONSTRAINT; Schema: public; Owner: sumin_translator
--

ALTER TABLE ONLY rating
    ADD CONSTRAINT translation FOREIGN KEY (translation_id) REFERENCES translation(id);


--
-- Name: public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM postgres;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- PostgreSQL database dump complete
--
