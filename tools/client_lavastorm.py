"""Read the reviewed Classic Lavastorm terrain without modifying source clients."""
import hashlib

PINNED={
    'lavastorm.s3d':'daa1053f71320e1f5882417f3dadc0b65c55fb64c75f3a806bceb57bbceb24c3',
    'lavastorm_obj.s3d':'6476962179483d940cde99ef60fee43477d95c158aa28ccc1bc0e14d396b7b1f',
}


def lavastorm_files(terrain,client):
    files={}
    for name,expected in PINNED.items():
        path=terrain if name=='lavastorm.s3d' else client/name
        data=path.read_bytes()
        if hashlib.sha256(data).hexdigest()!=expected:
            raise ValueError('Unsupported Classic Lavastorm archive: '+name)
        files[name]=data
    return files
