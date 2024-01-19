-- Update missing projectDistrict_id with infraohjelmointi_api_projectdistrict.id
-- This need to be done, because original Excel files uses old location information

UPDATE infraohjelmointi_api_project 
SET "projectDistrict_id" = infraohjelmointi_api_projectdistrict.id
FROM infraohjelmointi_api_projectdistrict, infraohjelmointi_api_projectlocation
WHERE infraohjelmointi_api_project."projectLocation_id" = infraohjelmointi_api_projectlocation.id
AND infraohjelmointi_api_projectlocation.path = infraohjelmointi_api_projectdistrict.path;

-- Update missing location_id with infraohjelmointi_api_projectdistrict.id

UPDATE infraohjelmointi_api_projectgroup
SET "location_id" = infraohjelmointi_api_projectdistrict.id
FROM infraohjelmointi_api_projectdistrict, infraohjelmointi_api_projectlocation
WHERE infraohjelmointi_api_projectgroup."locationRelation_id" = infraohjelmointi_api_projectlocation.id
AND infraohjelmointi_api_projectlocation.path = infraohjelmointi_api_projectdistrict.path;
