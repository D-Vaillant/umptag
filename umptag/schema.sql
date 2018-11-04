DROP TABLE IF EXISTS files;
CREATE TABLE files (
    id integer PRIMARY KEY,
    directory text NOT NULL,
    name text NOT NULL,
    size integer,
    mod_time timestamp,
    is_dir boolean,
    CONSTRAINT path UNIQUE (directory, name)
);

DROP TABLE IF EXISTS tags;
CREATE TABLE tags (
    id integer PRIMARY KEY,
    key text DEFAULT '' NOT NULL,
    value text NOT NULL,
    CONSTRAINT tag_pk UNIQUE (key, value)
);

DROP TABLE IF EXISTS filetag_junction;
CREATE TABLE filetag_junction (
    file_id int, tag_id int,
    CONSTRAINT file_tag_pk PRIMARY KEY (file_id, tag_id),
    CONSTRAINT FK_files
    FOREIGN KEY (file_id) REFERENCES files (id),
    CONSTRAINT FK_tags
    FOREIGN KEY (tag_id) REFERENCES tags (id)
);
