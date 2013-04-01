#!/usr/bin/env python
from monkeybook import celery

if __name__ == '__main__':
    # gevent pool does not implement restart
    # argv = ['./runcelery.py', '-l', 'INFO', '--autoreload']
    argv = ['./runcelery.py', '-l', 'INFO']
    celery.worker_main(argv)
