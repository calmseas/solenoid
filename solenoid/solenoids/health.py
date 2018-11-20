import os

THRESHOLD = 10485760

def get_disk_health(path):
    res = os.statvfs(path)
    if res.f_frsize*res.f_bavail < THRESHOLD:
        return {
            'status': 'DOWN',
            'details': {
                'total': res.f_frsize * res.f_blocks,
                'free': res.f_frsize * res.f_bavail,
                'threshold': THRESHOLD
            }
        }

    return {
        'status': 'UP',
        'details': {
            'total': res.f_frsize*res.f_blocks,
            'free': res.f_frsize*res.f_bavail,
            'threshold': THRESHOLD
        }
    }
