package ca.dmoj.java;

import java.io.File;
import java.io.FilePermission;
import java.lang.reflect.ReflectPermission;
import java.security.AccessControlException;
import java.security.Permission;
import java.util.PropertyPermission;

public class SubmissionSecurityManager extends SecurityManager {
    @Override
    public void checkPermission(Permission perm) {
        if (JavaSafeExecutor._safeBlock || Thread.currentThread() == JavaSafeExecutor.selfThread || Thread.currentThread() == JavaSafeExecutor.shockerThread) return;
        String fname = perm.getName().replace("\\", "/");
        if (perm instanceof FilePermission) {
            if (perm.getActions().equals("read") &&
                    (fname.startsWith(JavaSafeExecutor.cwd + File.separator) ||
                            fname.startsWith("/usr/lib/jvm/") ||
                            fname.contains("/jre/lib/zi/")
                    )) // Date
                return;
        }
        if (perm instanceof RuntimePermission) {
            if (fname.equals("writeFileDescriptor") ||
                    fname.equals("readFileDescriptor") ||
                    fname.equals("fileSystemProvider"))
                return;
            if (fname.startsWith("accessClassInPackage")) {
                if (fname.contains("sun.util.resources"))
                    return;
            }
        }
        if (perm instanceof ReflectPermission) {
            /*
                Java's Date API requires reflection.
                Thankfully this is safe enough, since it doesn't allow a malicious submission
                to access JavaSafeExecutor fields.
             */
            if (fname.equals("suppressAccessChecks")) {
                return;
            }
        }
        if (perm instanceof PropertyPermission) {
            if (perm.getActions().contains("write")) {
                if (fname.equals("user.timezone")) return; // Date
                throw new AccessControlException(perm.getClass() + " - " + perm.getName() + ": " + perm.getActions(), perm);
            }
            return;
        }
        throw new AccessControlException(perm.getClass() + " - " + perm.getName() + ": " + perm.getActions(), perm);
    }
}
