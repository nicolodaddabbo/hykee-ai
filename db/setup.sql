CREATE DATABASE hykee_ai;
GO

USE hykee_ai;
GO

CREATE TABLE hykee_ai_evaluation (
    id INT NOT NULL,
    llm VARCHAR(255) NOT NULL,
    method_name VARCHAR(255) NOT NULL,
    prompt TEXT NOT NULL,
    context TEXT NOT NULL,
    answer TEXT NOT NULL,
    human_score INT,
    llm_score INT,
    PRIMARY KEY (id, llm, method_name)
);
