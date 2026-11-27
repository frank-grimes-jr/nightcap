param([ValidateSet('baseline','candidate')][string]$Stage = 'candidate')
$ErrorActionPreference = 'Stop'
$workspace = 'E:/EQ_Local_Dev'
$fixture = Join-Path $workspace 'artifacts/cairnwright-creation-20261121'
$account = Import-Clixml (Join-Path $fixture 'hailstone-qa-account.clixml')
if ($account.UserName -notmatch '^ncqa[a-z]{5}$') { throw 'Disposable account identity mismatch' }
$sql = "SELECT c.name FROM character_data c JOIN account a ON a.id=c.account_id WHERE a.name='$($account.UserName)' AND c.class=17 AND c.race=8 AND c.level=1 AND c.zone_id=22 ORDER BY c.id LIMIT 1"
$character = docker exec akk-stack-mariadb-1 mariadb --defaults-extra-file=/run/local-secrets/client.cnf -NB peq -e $sql
if ($LASTEXITCODE -ne 0 -or $character -notmatch '^Tor[a-z]{5}$') { throw 'Disposable primary Cairnwright unavailable' }
$env:NIGHTCAP_QA_ACCOUNT = $account.UserName
$env:NIGHTCAP_QA_PASSWORD = $account.GetNetworkCredential().Password
$env:NIGHTCAP_QA_CHARACTER = $character
try {
    python -B (Join-Path $PSScriptRoot 'verify_recall.py') $Stage
    if ($LASTEXITCODE -ne 0) { throw 'LocalDev Recall check failed' }
} finally {
    Remove-Item Env:NIGHTCAP_QA_PASSWORD,Env:NIGHTCAP_QA_ACCOUNT,Env:NIGHTCAP_QA_CHARACTER -ErrorAction SilentlyContinue
}

