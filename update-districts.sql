--hankkeiden suurpiirit
--jos projectLocation_id tyhjä, älä tee mitään
--jos projectLocation_id ei ole tyhjä:
--projectLocation taulusta haetaan ID:llä mikä se on
--otetaan path
--haetaan pathilla projectdistrictistä == path
--projectdistrictistä id, syötetään projectDistrict_id
UPDATE infraohjelmointi_api_project 
SET "projectDistrict_id" = infraohjelmointi_api_projectdistrict.id
FROM infraohjelmointi_api_projectdistrict, infraohjelmointi_api_projectlocation
WHERE infraohjelmointi_api_project."projectLocation_id" = infraohjelmointi_api_projectlocation.id
AND infraohjelmointi_api_projectlocation.path = infraohjelmointi_api_projectdistrict.path
AND infraohjelmointi_api_project."projectLocation_id" IS NOT NULL;


--ryhmien suurpiirit projectgroup
--jos locationRelation_id tyhjä, älä tee mitään
--jos locationRelation_id ei ole tyhjä:
--projectLocation taulusta haetaan ID:llä mikä se on
--otetaan path
--haetaan pathilla projectdistrictistä == path
--projectdistrictistä id, syötetään projectgroupiin location_id
UPDATE infraohjelmointi_api_projectgroup
SET "location_id" = infraohjelmointi_api_projectdistrict.id
FROM infraohjelmointi_api_projectdistrict, infraohjelmointi_api_projectlocation
WHERE infraohjelmointi_api_project."projectLocation_id" = infraohjelmointi_api_projectlocation.id
AND infraohjelmointi_api_projectlocation.path = infraohjelmointi_api_projectdistrict.path
AND infraohjelmointi_api_projectgroup."locationRelation_id" IS NOT NULL;