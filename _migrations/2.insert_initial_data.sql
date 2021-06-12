PRAGMA foreign_keys = OFF;

BEGIN TRANSACTION;

INSERT INTO "author" ("firstname", "lastname")
VALUES ('Nikos', 'Bilalis');

INSERT INTO "category" ("title")
VALUES ('sports');

INSERT INTO "category" ("title")
VALUES ('politics');

INSERT INTO "article" ("title", "body", "creation_date", "publish_date", "author_id", "category_id")
VALUES ('Euro starts', 'Blah blah blah. ', '2021-06-01', '2021-06-11', 1, 1);

INSERT INTO "article" ("title", "body", "creation_date", "publish_date", "author_id", "category_id")
VALUES ('Euro ends', 'Blah blah blah. ', '2021-06-01', '2021-07-11', 1, 1);

COMMIT TRANSACTION;

PRAGMA foreign_keys = ON;
