## WBox - Sandboxing on Windows

On Linux, `ptbox` has a fine-grained control over user submissions by intercepting all system calls via the [`ptrace(2)`](http://linux.die.net/man/2/ptrace) API. Since a similar API does not exist on Windows, alternative methods must be used.

### Securing the Filesystem

For every submission, an unprivileged user is programatically created with [`NetUserAdd`](https://msdn.microsoft.com/en-us/library/windows/desktop/aa370649%28v=vs.85%29.aspx). This user has no initialized profile (i.e., no `C:\Users` directory and no registry). Untrusted user submissions are ran under this user, such that any malicious code is not able to tamper with the filesystem. This user is deleted after the submission terminates.

Naturally, the user needs to have read access to a directory (`tempdir` in the judge configuration). Typically, a small virtual disk may be mounted for the judge to use as a temporary storage device.

### Securing the Network

Submissions should not have access to network resources (they could use this to initiate DOS attacks, download answers, or perform any other myriad of unwanted things). A temporary firewall rule is added ([`INetFwRules`](https://msdn.microsoft.com/en-us/library/windows/desktop/aa365345%28v=vs.85%29.aspx)) for each submission binary, disallowing all internet access. The rule is cleaned up at the end of grading.

### Resource Limiting

User code is generally run under strict time and memory limits that must be enforced by the sandbox. Ideally, submissions should not be allowed to tamper with global settings (e.g., swapping the mouse buttons), and should not attempt to create UIs.

Windows has [Job objects](https://msdn.microsoft.com/en-us/library/windows/desktop/ms684147%28v=vs.85%29.aspx) that may be used for this purpose. A Job object with the desired limits is created, and the submission process is attached to it.

#### Caveats and Workarounds

At this point, one might think that a sandbox is complete: the filesystem is secured, submissions cannot access the network, and cannot tamper with user settings. There is, as always, a catch.

When [`CreateProcessWithLogonW`](https://msdn.microsoft.com/en-us/library/windows/desktop/ms682431%28v=vs.85%29.aspx) is used to spawn the submission process under an unprivileged user, the Secondary Logon Service (SLS) is invoked. This would not be an issue, except that it puts the process into its own Job object. Windows 8 added support for processes being part of multiple Job objects, but compatibility is important. The problem is worsened by the inexistence of an API to fetch the Job object associated with a process.

In WBox, this issue is circumvented by using undocumented `ntdll` API to enumerate all system handles. These are filtered by type, and for all Job handles [`IsProcessInJob`](https://msdn.microsoft.com/en-us/library/windows/desktop/ms684127%28v=vs.85%29.aspx) is called to determine which Job the user process belongs to. Once this SLS Job object is found, it must be modified to add our restrictions. Since Windows 8, Job objects may be chained; however, since backwards compatibility is important, we instead overwrite the SLS Job object with our own.

### Silencing Runtime Errors

In online judging, Runtime Error verdicts are common. Whenever a user submission crashes, Windows helpfully opens a dialog informing the host that "the process has stopped unexpectedly", and that Windows is "searching online for a solution". Since the dialog is modal, execution of the judge is stopped until the host manually closes the dialog.

Thankfully, the Windows API contains a [`SetErrorMode`](https://msdn.microsoft.com/en-us/library/windows/desktop/ms680621%28v=vs.85%29.aspx) that can indicate to the operating system that the submission can handle runtime errors itself. Calling `SetErrorMode` silences the dialogs, and since this property is inherited by child processes, setting the error mode for the judge process should be a global solution.

#### More Caveats and Workarounds

When `CreateProcessWithLogonW` is used, the created process is not considered a child of the calling process: it is created as a child of the Secondary Logon Service. Therefore, calling `SetErrorMode` on the judge will have no effect on submission processes.

A DLL must be injected into the user process to `SetErrorMode`.

### Further Restrictions

`win32k.sys` handles system calls pertaining to NtUser/GDI &mdash; calls that submissions to an online judge should never have to call. Since Windows 8, the Windows API has a [`SetProcessMitigationPolicy`](https://msdn.microsoft.com/en-us/library/windows/desktop/hh769088%28v=vs.85%29.aspx) that allows complete disabling of all `win32k.sys` calls. This property is not inheritable, and hence must be set by an injected DLL.

This feature is not critical, but does decrease attack surface of a judge (a number of exploits have been discovered using the `win32k` API).
