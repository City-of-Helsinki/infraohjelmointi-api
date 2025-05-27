--update Siltojen peruskorjaukset to Siltojen peruskorjaus ja uusiminen in name and path fields
UPDATE infraohjelmointi_api_projectclass
SET 
    name = REPLACE(name, 'Siltojen peruskorjaukset', 'Siltojen peruskorjaus ja uusiminen'),
    path = REPLACE(path, 'Siltojen peruskorjaukset', 'Siltojen peruskorjaus ja uusiminen')
WHERE name ilike '%Siltojen peruskorjaukset%';

--update Ranta-alueiden kunnostus to Tulvasuojelu ja rantarakenteet in name and path fields
UPDATE infraohjelmointi_api_projectclass
SET 
    name = REPLACE(name, 'Ranta-Alueiden kunnostus', 'Tulvasuojelu ja rantarakenteet'),
    path = REPLACE(path, 'Ranta-Alueiden kunnostus', 'Tulvasuojelu ja rantarakenteet')
where path ilike '%Ranta-alueiden kunnostus%';





