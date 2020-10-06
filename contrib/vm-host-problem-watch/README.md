# vm-host-problem-watch

Configurations with multiple judges may either sync problem data to all judges,
or have problem data be provided by a central server (via NFS, 9P, virtiofs,
etc.) These mounting schemes typically do not support the `inotify` facility,
so some mechanism of telling judges to scan for problem updates is necessary
if one wants to be able to add new problem data without requiring a judge
restart.

This script is one way this may be done, by setting up an `inotify` watch on
the problem data host, and notifying judges of problem updates via the judge
API.

## Example Usage

```bash
$ cat /code/judge-hosts-list
judge1.example.com:9998
judge2.example.com:9998
judge3.example.com:9998
$ ls /export/problems | head -n 5
apio
bbc
bkoi
broi
btoi
$ ./vm-host-problem-watch.sh /export/problems /code/judge-host-list
Tue Oct  6 22:17:37 UTC 2020: Start watching /export/problems, notifying /code/judge-host-list
Tue Oct  6 22:17:46 UTC 2020: Update problems [/export/problems/rgss/17/rgpc17p5/ MOVED_FROM init.yml]
Tue Oct  6 22:17:46 UTC 2020 [judge1.example.com:9998]: As you wish.
Tue Oct  6 22:17:46 UTC 2020 [judge2.example.com:9998]: As you wish.
Tue Oct  6 22:17:46 UTC 2020 [judge3.example.com:9998]: As you wish.
```
