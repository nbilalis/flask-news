PRAGMA foreign_keys = OFF;

BEGIN TRANSACTION;

DROP TABLE IF EXISTS "author";
DROP TABLE IF EXISTS "article";
DROP TABLE IF EXISTS "category";

CREATE TABLE "author" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "firstname" VARCHAR(50) NOT NULL,
    "lastname" VARCHAR(50) NOT NULL
);

CREATE TABLE "category" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "title" VARCHAR(20) NOT NULL
);

CREATE TABLE "article" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "title" VARCHAR(100) NOT NULL,
    "body" TEXT NOT NULL,
    "creation_date" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "publish_date" DATETIME NOT NULL,
    "author_id" INTEGER REFERENCES "author" ("id"),
    "category_id" INTEGER REFERENCES "category" ("id")
);

COMMIT TRANSACTION;

PRAGMA foreign_keys = ON;
