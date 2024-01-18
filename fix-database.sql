--Set correct location numbers
UPDATE infraohjelmointi_api_projectlocation SET name = '2. Kluuvi' WHERE name = '3. Kluuvi';
UPDATE infraohjelmointi_api_projectlocation SET name = '38. Malmi' WHERE name = '37. Malmi';
UPDATE infraohjelmointi_api_projectlocation SET name = '37. Pukinmäki' WHERE name = '38. Pukinmäki';

--Correct typos
UPDATE infraohjelmointi_api_projectclass SET name = REPLACE (name, 'Liikunta-Alueet', 'Liikunta-alueet');
UPDATE infraohjelmointi_api_projectclass SET path = REPLACE (path, 'Liikunta-Alueet', 'Liikunta-alueet');
UPDATE infraohjelmointi_api_projectclass SET name = REPLACE (name, 'Ranta-Alueiden', 'Ranta-alueiden');
UPDATE infraohjelmointi_api_projectclass SET path = REPLACE (path, 'Ranta-Alueiden', 'Ranta-alueiden');
UPDATE infraohjelmointi_api_projectclass SET name = REPLACE (name, 'väylävirasto', 'Väylävirasto');
UPDATE infraohjelmointi_api_projectclass SET path = REPLACE (path, 'väylävirasto', 'Väylävirasto');
UPDATE infraohjelmointi_api_projectclass SET name = REPLACE (name, 'kaupunkiympäristölautakunnan', 'Kaupunkiympäristölautakunnan');
UPDATE infraohjelmointi_api_projectclass SET path = REPLACE (path, 'kaupunkiympäristölautakunnan', 'Kaupunkiympäristölautakunnan');
UPDATE infraohjelmointi_api_projectclass SET name = REPLACE (name, 'kaupunkiympärstölautakunnan', 'Kaupunkiympäristölautakunnan');
UPDATE infraohjelmointi_api_projectclass SET name = REPLACE (name, 'kaupunkiympärstölautakunnan', 'Kaupunkiympäristölautakunnan');
UPDATE infraohjelmointi_api_projectclass SET name = REPLACE(name, 'umen vastaanottopaikat', 'umenvastaanottopaikat');
UPDATE infraohjelmointi_api_projectclass SET path = REPLACE(path, 'umen vastaanottopaikat', 'umenvastaanottopaikat');

--Add missing 'suurpiiri' text for locations (name -column)
UPDATE infraohjelmointi_api_projectlocation SET name = CONCAT(name, ' suurpiiri') WHERE name IN ('Eteläinen', 'Läntinen', 'Kaakkoinen', 'Keskinen', 'Pohjoinen', 'Koillinen', 'Itäinen') AND NOT name LIKE '%suurpiiri%';
UPDATE infraohjelmointi_api_projectlocation SET name = 'Östersundomin suurpiiri' WHERE name = 'Östersundom';

--Add missing 'suurpiiri' text for locations (path -column)
UPDATE infraohjelmointi_api_projectlocation SET path = REPLACE(path, 'Koillinen', 'Koillinen suurpiiri') WHERE path LIKE 'Koillinen%' AND NOT path LIKE '%suurpiiri%';
UPDATE infraohjelmointi_api_projectlocation SET path = REPLACE(path, 'Eteläinen', 'Eteläinen suurpiiri') WHERE path LIKE 'Eteläinen%' AND NOT path LIKE '%suurpiiri%';
UPDATE infraohjelmointi_api_projectlocation SET path = REPLACE(path, 'Läntinen', 'Läntinen suurpiiri') WHERE path LIKE 'Läntinen%' AND NOT path LIKE '%suurpiiri%';
UPDATE infraohjelmointi_api_projectlocation SET path = REPLACE(path, 'Keskinen', 'Keskinen suurpiiri') WHERE path LIKE 'Keskinen%' AND NOT path LIKE '%suurpiiri%';
UPDATE infraohjelmointi_api_projectlocation SET path = REPLACE(path, 'Pohjoinen', 'Pohjoinen suurpiiri') WHERE path LIKE 'Pohjoinen%' AND NOT path LIKE '%suurpiiri%';
UPDATE infraohjelmointi_api_projectlocation SET path = REPLACE(path, 'Kaakkoinen', 'Kaakkoinen suurpiiri') WHERE path LIKE 'Kaakkoinen%' AND NOT path LIKE '%suurpiiri%';
UPDATE infraohjelmointi_api_projectlocation SET path = REPLACE(path, 'Itäinen', 'Itäinen suurpiiri') WHERE path LIKE 'Itäinen%' AND NOT path LIKE '%suurpiiri%';
UPDATE infraohjelmointi_api_projectlocation SET path = REPLACE(path, 'Östersundom', 'Östersundomin suurpiiri') WHERE path LIKE 'Östersundom%' AND NOT path LIKE '%suurpiiri%';