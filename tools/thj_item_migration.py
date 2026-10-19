"""Compact full-row guarded item updates. No character or inventory statements."""
import hashlib,re
from rabid_bear import sql_value

def row_hash(row,columns):
    parts=['NULL' if row[c] is None else str(row[c]).encode('utf-8').hex().upper() for c in columns]
    return hashlib.sha256('|'.join(parts).encode('ascii')).hexdigest()

def migration(pairs,columns,alternate_before=None):
    if not pairs or len({old['id'] for old,new in pairs})!=len(pairs):raise ValueError('Empty/duplicate item plan')
    if any(not re.fullmatch('[A-Za-z_][A-Za-z0-9_]*',c) for c in columns):raise ValueError('Invalid schema identifier')
    from thj_item_parity import FIELDS
    fields=FIELDS|{'focuseffect','focustype','focuslevel','focuslevel2','focusname','worneffect','worntype','wornlevel','wornlevel2','wornname','nopet'}|{f'augslot{i}{suffix}' for i in range(1,7) for suffix in ('type','visible')}
    for old,new in pairs:
        if set(old)!=set(columns) or set(new)!=set(columns) or old['id']!=new['id']:raise ValueError('Full item preimages required')
        if {k for k in old if str(old[k])!=str(new[k])}-fields:raise ValueError('Migration touches unowned fields')
    expression="SHA2(CONCAT_WS('|',"+','.join("IFNULL(HEX(CAST(`"+c+"` AS CHAR CHARACTER SET utf8mb4)),'NULL')" for c in columns)+'),256)'
    name='nightcap_thj_items_20261018'
    lines=['SET NAMES utf8mb4;',f'DROP PROCEDURE IF EXISTS {name};',
           'DROP TEMPORARY TABLE IF EXISTS nightcap_thj_item_preimages;',
           'CREATE TEMPORARY TABLE nightcap_thj_item_preimages (id INT UNSIGNED PRIMARY KEY, before_hash CHAR(64) CHARACTER SET ascii, after_hash CHAR(64) CHARACTER SET ascii, companion_hash CHAR(64) CHARACTER SET ascii) ENGINE=InnoDB;',
           'INSERT INTO nightcap_thj_item_preimages VALUES '+','.join(f"({old['id']},'{row_hash(old,columns)}','{row_hash(new,columns)}','{row_hash(alternate_before[old['id']] if alternate_before else old,columns)}')" for old,new in pairs)+';',
           'DELIMITER //',f'CREATE PROCEDURE {name}()', 'BEGIN',
           ' DECLARE finished BOOL DEFAULT FALSE; DECLARE item_id INT UNSIGNED; DECLARE expected_before CHAR(64); DECLARE expected_after CHAR(64); DECLARE expected_companion CHAR(64); DECLARE actual_hash CHAR(64); DECLARE item_count INT;',
           ' DECLARE targets CURSOR FOR SELECT id,before_hash,after_hash,companion_hash FROM nightcap_thj_item_preimages ORDER BY id;',
           ' DECLARE CONTINUE HANDLER FOR NOT FOUND SET finished=TRUE;',
           ' DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;',
           ' SET TRANSACTION ISOLATION LEVEL SERIALIZABLE; START TRANSACTION;',
           " IF (SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='items' AND ENGINE='InnoDB')<>1 OR EXISTS(SELECT 1 FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA=DATABASE() AND EVENT_OBJECT_TABLE='items') THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Unexpected item storage'; END IF;",
           f" IF (SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='items')<>{len(columns)} THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Item schema drift'; END IF;",
           ' OPEN targets; preflight: LOOP',
           ' FETCH targets INTO item_id,expected_before,expected_after,expected_companion; IF finished THEN LEAVE preflight; END IF;',
           ' SELECT COUNT(*) INTO item_count FROM items WHERE id=item_id;',
           " IF item_count<>1 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Missing item identity'; END IF;",
           f' SELECT {expression} INTO actual_hash FROM items WHERE id=item_id FOR UPDATE;',
           " IF actual_hash<>expected_before AND actual_hash<>expected_after AND actual_hash<>expected_companion THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Item full preimage drift'; END IF;",
           ' END LOOP; CLOSE targets;']
    for old,new in pairs:
        changed={k:v for k,v in new.items() if str(old[k])!=str(v)}
        if changed:lines.append(' UPDATE items SET '+','.join('`'+k+'`='+sql_value(v) for k,v in changed.items())+' WHERE id='+str(old['id'])+';')
    lines+=[' SET finished=FALSE; OPEN targets; verify_rows: LOOP',
            ' FETCH targets INTO item_id,expected_before,expected_after,expected_companion; IF finished THEN LEAVE verify_rows; END IF;',
            f' SELECT {expression} INTO actual_hash FROM items WHERE id=item_id;',
            " IF actual_hash<>expected_after THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Item afterimage mismatch'; END IF;",
            ' END LOOP; CLOSE targets; COMMIT; END//','DELIMITER ;',f'CALL {name}();',f'DROP PROCEDURE {name};','DROP TEMPORARY TABLE nightcap_thj_item_preimages;','']
    return '\n'.join(lines)
