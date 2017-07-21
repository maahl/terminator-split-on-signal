# Terminator SplitOnSignal

This is a plugin for Terminator, that makes it split the last focused terminal
upon receiving the signal SIGUSR1 (vertical split) or SIGUSR2 (horizontal
split). After splitting, the plugin listens for a command on a port (see the
variable `LISTEN_PORT` to know which one) for a command to be executed in the
new terminal. This allows you to start stuff programmatically.

## Installation

To load this plugin, simply put it in `~/.config/terminator/plugins` and enable
it in Terminator preferences.

## Example usage:

Basic example:
```sh
# split vertically the last opened terminator instance and run the command `ls` in
# the new terminal
pkill -SIGUSR1 -n terminator && until echo ls | nc -N localhost 5198; do sleep 0.5; done
```

Real-life example: I have this in my config file for psql, so that it starts gdb
on the backend for my current postgresql session (the server must be on the same
machine as the client), to debug postgres.

```
\set gdb 'SELECT pg_backend_pid() \\g | grep -E "[0-9]{2,}" | tr -d " " | awk \'{system("pkill -SIGUSR1 -n terminator && until echo gdb --pid=" $0 | nc -N localhost 5198; do sleep 0.5; done")}\''
```

This retrieves the PID of the backend and pipes it to a shell, which then splits
the current terminal (containing psql), and attaches gdb to the backend in the
new terminal.
