DROP TABLE IF EXISTS "consultas";
DROP TABLE IF EXISTS "medico";

CREATE TABLE "medico" (
    "id" SERIAL PRIMARY KEY,
    "nome" VARCHAR(255) NOT NULL,
    "crm" VARCHAR(255) NOT NULL,
    "especialidade" VARCHAR(255) NOT NULL
);

CREATE TABLE "consultas" (
    "id" SERIAL PRIMARY KEY,
    "medico_id" INTEGER REFERENCES medico(id) ON DELETE CASCADE,
    "data" VARCHAR(255) NOT NULL,
    "valor" VARCHAR(255) NOT NULL,
    "tipo" VARCHAR(255) NOT NULL,
    "convenio" VARCHAR(255) NOT NULL
);

INSERT INTO "medico" ("nome", "crm", "especialidade") VALUES ('Batatinha', '123', 'Clínico Geral');
INSERT INTO "medico" ("nome", "crm", "especialidade") VALUES ('Zan', '456', 'Neurologista');
INSERT INTO "medico" ("nome", "crm", "especialidade") VALUES ('RenZo', '789', 'Cardiologista');