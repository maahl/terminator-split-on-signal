#!/usr/bin/env python

'''
Terminator plugin that splits the last focused terminal vertically or
horizontally upon receiving a SIGUSR1 or SIGUSR2. After that, it listens on a
port for a command to be run.
'''

import signal
import socket
import sys
from gi.repository import GLib, Vte
from terminatorlib.container import Container
from terminatorlib.plugin import Plugin
from terminatorlib.terminal import Terminal
from terminatorlib.terminator import Terminator
from terminatorlib.util import dbg, inject_uuid

AVAILABLE = ['SplitOnSignal']

LISTEN_PORT = 5198

class SplitOnSignal(Plugin):
    capabilities = ['signal_handler']

    def __init__(self):
        self.terminator = Terminator()
        dbg('map signal SIGUSR1 to vertical split and SIGUSR2 to horizontal split')
        signal.signal(signal.SIGUSR1, self.handle_sigusr)
        signal.signal(signal.SIGUSR2, self.handle_sigusr)

    def get_terminal_container(self, terminal, container=None):
        terminator = self.terminator
        if not container:
            for window in terminator.windows:
                owner = self.get_terminal_container(terminal, window)
                if owner: return owner
        else:
            for child in container.get_children():
                if isinstance(child, Terminal) and child == terminal:
                    return container
                if isinstance(child, Container):
                    owner = self.get_terminal_container(terminal, child)
                    if owner: return owner

    def split(self, terminal, horizontal=False):
        container = self.get_terminal_container(terminal)

        sibling = Terminal()
        inject_uuid(sibling)
        cwd = self.terminator.pid_cwd(terminal.pid)
        sibling.set_cwd(cwd)
        container.split_axis(terminal, horizontal, cwd=None, sibling=sibling)
        sibling.vte.spawn_sync(Vte.PtyFlags.DEFAULT, cwd, ['/usr/bin/zsh'], None, GLib.SpawnFlags.SEARCH_PATH_FROM_ENVP, None, None, None)

        return sibling

    def handle_sigusr(self, sig, frame):
        try:
            #import ipdb; ipdb.set_trace()
            # retrieve the command the new terminal should execute
            cmd = self.read_command()

            # split the last encountered terminal
            terminal = self.get_most_recent_terminal()
            if sig == signal.SIGUSR1:
                dbg('received signal SIGUSR1, splitting last focused terminal vertically')
                new_terminal = self.split(terminal, horizontal=False)
            elif sig == signal.SIGUSR2:
                dbg('received signal SIGUSR2, splitting last focused terminal horizontally')
                new_terminal = self.split(terminal, horizontal=True)

            # send the command to be executed to the new terminal
            new_terminal.vte.feed_child(cmd, len(cmd))
        except Exception as e:
            dbg(e)

    def get_most_recent_terminal(self):
        terminal = self.terminator.get_focussed_terminal()
        if terminal is None:
            terminal = self.terminator.last_focused_term

        return terminal

    def read_command(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('localhost', LISTEN_PORT))
        s.listen(0)

        cmd = ''
        dbg('ready to receive a command')
        conn, _ = s.accept()
        while True:
            data = conn.recv(1024)
            if not data:
                break
            else:
                dbg(data)
                cmd += data
        conn.close()

        if not cmd.endswith('\n'):
            cmd = 'sh -c ' + cmd + '\n'

        return cmd
