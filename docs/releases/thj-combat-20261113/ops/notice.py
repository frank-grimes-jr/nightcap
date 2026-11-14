"""Queue at most one short maintenance notice through the native world event scheduler."""
import json
from probe import LOAD, STAGE, remote, write

MESSAGE = ("Nightcap maintenance is ready to deploy the bow and Backstab update. "
           "Please camp when it is safe so we can restart. We will reopen after verification. Thank you.")

CODE = """
import datetime, time, fcntl, subprocess, hashlib
root=Path('/opt/nightcap/releases')/stage
receipt=root/'maintenance-notice.json'
label='Nightcap combat maintenance '+stage
def literal(s): return "X'"+s.encode().hex()+"'"
assert '%' not in message and len(message)<240
with (prior.ROOT/'.deployment.lock').open('a') as lock, open('/var/lock/nightcap-gm.lock','a') as gm:
    for f in (lock,gm):
        fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
    if receipt.exists():
        print(json.dumps(prior.read(receipt)))
        raise SystemExit
    count=prior.a.prior.players()
    if not count:
        print(json.dumps(dict(queued=False,players=0)))
        raise SystemExit
    assert not (prior.ROOT/'private/gm-maintenance.json').exists() and prior.sql("SELECT IS_FREE_LOCK('nightcap_gm_writes')").strip()=='1'
    g=prior.r.compact('game')
    assert prior.r.compact('gateway')['running'] and g['image_id']==prior.read(prior.ACTIVE/'deployed.json')['image']
    assert prior.sql('SELECT COUNT(*) FROM server_scheduled_events WHERE BINARY description='+literal(label)).strip()=='0'
    baseline=prior.a.prior.digest('server_scheduled_events')
    # Use the game's own local clock. Schedule the next full minute, leaving a
    # complete setup interval when the current minute is about to end.
    clock=subprocess.check_output(['docker','exec',g['id'],'date','+%Y-%m-%dT%H:%M:%S'],text=True).strip()
    now=datetime.datetime.fromisoformat(clock)
    start=now.replace(second=0,microsecond=0)+datetime.timedelta(minutes=(2 if now.second>54 else 1))
    end=start+datetime.timedelta(minutes=1)
    # Cron uses the world process clock and executes when next schedule is
    # within 10s. Use literal dates/hour bounds by default, including an
    # exact-minute cron alternative on the native midnight/zero sentinel.
    cron=''
    if end.minute==0 or start.minute==0 or start.hour==0 or end.hour==0:
        cron=f'8 {start.minute} {start.hour} {start.day} {start.month} *'
    values=[start.minute,start.hour,start.day,start.month,start.year,end.minute,end.hour,end.day,end.month,end.year]
    fields='minute_start,hour_start,day_start,month_start,year_start,minute_end,hour_end,day_end,month_end,year_end'
    query='INSERT INTO server_scheduled_events(description,event_type,event_data,'+fields+',cron_expression,created_at) VALUES ('+','.join([literal(label),literal('broadcast'),literal(message),*map(str,values),literal(cron),'NOW()'])+'); SELECT LAST_INSERT_ID();'
    prior.save(receipt,dict(queued='attempted',message=message,start=str(start),end=str(end),players=count))
    result=prior.sql(query).strip()
    assert result.isdigit() and int(result)>0
    pk=int(result)
    filt=f'id={pk} AND BINARY description='+literal(label)+' AND BINARY event_data='+literal(message)+" AND event_type='broadcast'"
    assert prior.sql('SELECT COUNT(*) FROM server_scheduled_events WHERE '+filt).strip()=='1'
    since=str(int(time.time())-5)
    sent=0
    deadline=time.monotonic()+(end-now).total_seconds()+5
    try:
        while time.monotonic()<deadline:
            logs=prior.r.out('docker','compose','logs','--no-color','--since',since,'game')
            sent=logs.count('Sending broadcast ['+message+']')
            if sent: break
            # Native world can send its scheduler category only to file.
            files=list((prior.ROOT/'data/server/logs').glob('world_*.log'))
            if files:
                newest=max(files,key=lambda p:p.stat().st_mtime)
                with newest.open('rb') as f:
                    f.seek(max(0,newest.stat().st_size-250000))
                    sent=f.read().count(('Sending broadcast ['+message+']').encode())
            if sent: break
            time.sleep(3)
    finally:
        assert prior.sql('DELETE FROM server_scheduled_events WHERE '+filt+'; SELECT ROW_COUNT();').strip()=='1'
        assert prior.a.prior.digest('server_scheduled_events')==baseline
    outcome=dict(queued=True,world_dispatch_log_matches=sent,players_at_queue=count,
                 message=message,start_game_time=str(start),end_game_time=str(end),event_id=pk,
                 receipt_id=hashlib.sha256(receipt.read_bytes()).hexdigest(),event_removed=True)
    prior.save(root/'maintenance-notice-result.json',outcome)
    print(json.dumps(outcome))
"""


if __name__ == "__main__":
    data = json.loads(remote("stage="+repr(STAGE)+"\nmessage="+repr(MESSAGE)+"\n"+LOAD+CODE,timeout=420))
    write("maintenance-notice.json",data)
    print(json.dumps(data))
