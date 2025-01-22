-- Add a new project type 'preConstruction'

INSERT INTO infraohjelmointi_api_projecttype (id, value, "createdDate", "updatedDate") 
VALUES (gen_random_uuid(), 'preConstruction', NOW(), NOW());
