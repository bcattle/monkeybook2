#!/usr/bin/env python
from monkeybook import celery

if __name__ == '__main__':
    argv = ['./runcelery.py', '-l', 'INFO', '--autoreload']
    celery.worker_main(argv)
