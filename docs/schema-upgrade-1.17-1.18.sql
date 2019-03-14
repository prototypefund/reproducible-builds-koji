-- upgrade script to migrate the Koji database schema
-- from version 1.16 to 1.17


BEGIN;

-- add tgz to list of tar's extensions
UPDATE archivetypes SET extensions = 'tar tar.gz tar.bz2 tar.xz tgz' WHERE name = 'tar';

COMMIT;
