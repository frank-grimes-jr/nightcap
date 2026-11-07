# Character attunement/cooldown only. Native tasks own earned progress.
use strict;
use warnings;

sub epic05_statement {
    my ($kind, $sql, @parameters) = @_;
    my $result;
    my $ok = eval {
        my $db = Database->new();
        my $statement = $db->prepare($sql) or die 'prepare failed';
        $statement->execute(@parameters); # Native execute returns void.
        if ($kind eq 'read') {
            my $row = $statement->fetch_hashref();
            $result = $row ? {%$row} : {};
        } else {
            $result = $statement->rows_affected();
        }
        1;
    };
    if (!$ok) {
        warn "[Epic05] Database operation failed; action refused. $@";
        return;
    }
    return $result;
}

sub epic05_store_enabled {
    my $row = epic05_statement('read',
        'SELECT enabled FROM nightcap_epic05_control WHERE id=1 AND native_contract=1 AND catalog_version=1');
    return $row && ($row->{enabled} // 0) == 1;
}

sub epic05_store_state {
    my ($character_id) = @_;
    my $row = epic05_statement('read',
        'SELECT active_path,GREATEST(CAST(ready_at AS SIGNED)-UNIX_TIMESTAMP(),0) AS remaining '
        . 'FROM nightcap_epic05_state WHERE character_id=?', $character_id);
    return unless $row;
    return $row->{active_path} ? $row : {active_path => '', remaining => 0};
}

sub epic05_store_earned {
    my ($character_id, $path_task) = @_;
    return 0 unless defined($path_task) && $path_task =~ /^950[3-7]$/;
    my $row = epic05_statement('read',
        'SELECT COUNT(DISTINCT taskid) AS earned FROM completed_tasks '
        . 'WHERE charid=? AND activityid=-1 AND taskid IN (9500,9501,9502,?)',
        $character_id, $path_task);
    return $row && ($row->{earned} // 0) == 4;
}

sub epic05_store_attune {
    my ($character_id, $path) = @_;
    my $state = epic05_store_state($character_id);
    return 0 unless $state && !$state->{remaining};
    return 1 if $state->{active_path} eq $path;
    my $statement;
    if (!$state->{active_path}) {
        $statement = epic05_statement('write',
            'INSERT INTO nightcap_epic05_state (character_id,active_path) '
            . 'SELECT ?,? FROM nightcap_epic05_control WHERE id=1 AND enabled=1 AND native_contract=1 AND catalog_version=1',
            $character_id, $path);
    } else {
        $statement = epic05_statement('write',
            'UPDATE nightcap_epic05_state SET active_path=? '
            . 'WHERE character_id=? AND active_path=? AND ready_at<=UNIX_TIMESTAMP() '
            . 'AND EXISTS (SELECT 1 FROM nightcap_epic05_control WHERE id=1 AND enabled=1 AND native_contract=1 AND catalog_version=1)',
            $path, $character_id, $state->{active_path});
    }
    return defined($statement) && $statement == 1;
}

sub epic05_store_reserve {
    my ($character_id, $path) = @_;
    # One autocommitted compare-and-set. Do not retry an uncertain result.
    my $statement = epic05_statement('write',
        'UPDATE nightcap_epic05_state SET ready_at=UNIX_TIMESTAMP()+600,uses=uses+1 '
        . 'WHERE character_id=? AND active_path=? AND ready_at<=UNIX_TIMESTAMP() '
        . 'AND EXISTS (SELECT 1 FROM nightcap_epic05_control WHERE id=1 AND enabled=1 AND native_contract=1 AND catalog_version=1)',
        $character_id, $path);
    return defined($statement) && $statement == 1;
}

1;
