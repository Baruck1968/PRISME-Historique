"""Exclusive cross-process locks on Linux and native Windows; no lock deletion.

Windows uses a one-byte OS lock, released on close/process exit. All PRISME
processes must share this implementation and the same private filesystem.
"""
from contextlib import contextmanager
import errno
import os
from pathlib import Path
import time

IS_WINDOWS=(os.name=='nt')

@contextmanager
def locked(root, timeout=30.0):
    root=Path(root)
    root.mkdir(parents=True,exist_ok=True)
    with (root/'.lock').open('a+b',buffering=0) as stream:
        if os.fstat(stream.fileno()).st_size==0:
            stream.write(b'\0')
        stream.seek(0)
        if IS_WINDOWS:
            import msvcrt
            def acquire():
                stream.seek(0);msvcrt.locking(stream.fileno(),msvcrt.LK_NBLCK,1)
            def release():
                stream.seek(0);msvcrt.locking(stream.fileno(),msvcrt.LK_UNLCK,1)
        else:
            import fcntl
            def acquire():fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
            def release():fcntl.flock(stream,fcntl.LOCK_UN)
        deadline=time.monotonic()+timeout
        while True:
            try:
                acquire();break
            except OSError as exc:
                if exc.errno not in (errno.EACCES,errno.EAGAIN,errno.EDEADLK):raise
                if time.monotonic()>=deadline:raise TimeoutError('Private state lock unavailable') from None
                time.sleep(0.05)
        try:yield
        finally:release()
