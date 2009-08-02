CREATE OR REPLACE FUNCTION update_place(integer, integer, varchar, varchar, integer, integer, geometry, timestamp without time zone, varchar) RETURNS boolean AS $_$
DECLARE
    p_source ALIAS FOR $1;
    p_external_code ALIAS FOR $2;
    p_name ALIAS FOR $3;
    p_name_ascii ALIAS FOR $4;
    p_country_id ALIAS FOR $5;
    p_administrative_division_id ALIAS FOR $6;
    p_coords ALIAS FOR $7;
    p_date_modified_external ALIAS FOR $8;
    p_names ALIAS FOR $9;
    v_place_id integer;
    r record;
BEGIN
    SELECT INTO v_place_id id FROM travelist_place WHERE source = p_source AND external_code = p_external_code;
    IF v_place_id IS NULL THEN
        INSERT INTO travelist_place (source, external_code, name, name_ascii, country_id, administrative_division_id, coords, date_modified_external)
            VALUES (p_source, p_external_code, p_name, p_name_ascii, p_country_id, p_administrative_division_id, p_coords, p_date_modified_external);
        FOR r IN SELECT * FROM regexp_split_to_table(p_names, E',') LOOP
            INSERT INTO travelist_placename (place_id, source, name) VALUES (currval('travelist_place_id_seq'), p_source, r.regexp_split_to_table);
        END LOOP;
        UPDATE __geonames_update_place SET added = added + 1;
        RETURN true;
    ELSE
        IF (SELECT date_modified_external IS NULL OR date_modified_external < p_date_modified_external FROM travelist_place WHERE id = v_place_id) THEN
            UPDATE travelist_place SET name = p_name, name_ascii = p_name_ascii, coords = p_coords, date_modified_external = p_date_modified_external
                WHERE id = v_place_id;
            DELETE FROM travelist_placename WHERE place_id = v_place_id;
            FOR r IN SELECT * FROM regexp_split_to_table(p_names, E',') LOOP
                INSERT INTO travelist_placename (place_id, source, name) VALUES (v_place_id, p_source, r.regexp_split_to_table);
            END LOOP;
            UPDATE __geonames_update_place SET updated = updated + 1;
            RETURN true;
        END IF;
    END IF;
    UPDATE __geonames_update_place SET unchanged = unchanged + 1;
    RETURN false;
END;$_$
LANGUAGE 'plpgsql';