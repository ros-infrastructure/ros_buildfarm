#!/usr/bin/env python3

"""
This scripts monitors a specific process and ensures that its child processes
are terminated correctly.
If any child process is a 'docker run' invocation it extracts the container id
from the command line arguments and invokes 'docker kill' explicitly.
"""

from __future__ import print_function

import argparse
import os
import psutil
import signal
import subprocess
import sys
import time


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(
        description='Monitor all subprocesses of a given process id and ' +
                    'ensure that they are terminated when the parent ' +
                    'process dies.')
    parser.add_argument(
        'pid', type=int, nargs='?', default=os.getppid(),
        help='The process ID to monitor (default: id of parent process)')
    args = parser.parse_args(argv)

    mypid = os.getpid()

    # check if PID is valid
    try:
        proc = psutil.Process(args.pid)
    except psutil.NoSuchProcess:
        print('No process with ID %i found' % args.pid, file=sys.stderr)
        return 1

    # wait until monitored process has died
    print('Monitoring PID %i...' % args.pid)
    children = []
    while proc.is_running():
        try:
            children = proc.get_children(recursive=True)
        except psutil.NoSuchProcess:
            continue
        # don't use small sleep values like 0.25s
        # since that results in a high CPU load
        time.sleep(10)

    # remove myself from list of children
    children = [c for c in children if c.pid != mypid]

    if not children:
        print('No child processes to terminate.')
        return 0

    if children:
        docker_run_cid_files = []
        print("Searching for 'docker run' child processes...")
        for c in children:
            try:
                cmdline = c.cmdline
            except psutil.NoSuchProcess:
                continue
            if cmdline[0] == 'docker' and cmdline[1] == 'run':
                cid_prefix = '--cidfile='
                for arg in cmdline[2:]:
                    if arg.startswith(cid_prefix):
                        docker_run_cid_files.append(arg[len(cid_prefix):])
                        print('- %s: %s' %
                              (docker_run_cid_files[-1], ' '.join(cmdline)))
                        break
        if docker_run_cid_files:
            print("Sending KILL signal to %i docker containers:" %
                  len(docker_run_cid_files))
            for cid_file in docker_run_cid_files:
                with open(cid_file, 'r') as h:
                    cid = h.read()
                    try:
                        subprocess.check_call(['docker', 'kill', cid])
                        print('- %s: %s' % (cid, cid_file))
                    except subprocess.CalledProcessError as e:
                        print("Docker container '%s' could not be killed: %s" %
                              (cid, e), file=sys.stderr)

        print('Sending TERM signal to %i child processes:' % len(children))
        for c in children:
            try:
                c.terminate()
                print('- %i: %s' % (c.pid, c.name))
            except psutil.NoSuchProcess:
                print('- %i (already terminated)' % c.pid)

        # wait until all processes are no longer running
        # or until timeout has elapsed
        # giving the processes time to handle the TERM signal
        children = wait_for_processes(children, 30.0)

    if children:
        print('Sending KILL signal to %i remaining child processes:' %
              len(children))
        for c in children:
            try:
                c.kill()
                print('- %i: %s' % (c.pid, c.name))
            except psutil.NoSuchProcess:
                print('- %i (already terminated)' % c.pid)

        # wait again to check if all process are no longer running
        # giving some time so that the KILL signals have been handled
        # (e.g. should not be 0.1s)
        children = wait_for_processes(children, 1.0)

    if children:
        print('%i processes could not be killed:' % len(children),
              file=sys.stderr)
        for c in children:
            try:
                print('- %i: %s' % (c.pid, c.name), file=sys.stderr)
            except psutil.NoSuchProcess:
                print('- %i (terminated by now)' % c.pid)
        return 1

    print('All processes have been terminated.')
    return 0


def wait_for_processes(processes, timeout=1.0):
    # wait until the processes are no longer running or the timeout has elapsed
    print('Waiting %is for processes to end:' % timeout)
    endtime = time.time() + timeout
    while time.time() < endtime and processes:
        time.sleep(0.1)
        not_running = [p for p in processes if not p.is_running()]
        for p in not_running:
            print('- %i' % p.pid)
        processes = [p for p in processes if p not in not_running]
    return processes


if __name__ == '__main__':
    # ignore SIGTERM so that if the parent process is killed
    # and forwards the signal, this script does not die
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    sys.exit(main())
