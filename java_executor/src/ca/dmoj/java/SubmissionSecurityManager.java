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
                    (fname.toLowerCase().endsWith(".class") ||
                            fname.startsWith("/usr/lib/jvm/") ||
                            fname.contains("/jre/lib/zi/")
                    )) // Date
                return;
        }
        if (perm instanceof RuntimePermission) {
            if (fname.equals("writeFileDescriptor") ||
                    fname.equals("readFileDescriptor") ||
                    fname.equals("fileSystemProvider") ||
                    fname.equals("getProtectionDomain") ||
                    fname.equals("accessDeclaredMembers"))
                return;
            if (fname.startsWith("accessClassInPackage")) {
                if (fname.contains("sun.util.resources"))
                    return;
            }
        }
        if (perm instanceof ReflectPermission) {
            /*
                Java's Date API requires reflection.
             */
            return;
        }
        if (perm instanceof PropertyPermission) {
            if (perm.getActions().contains("write")) {
                if (fname.equals("user.timezone")) return; // Date
                if (fname.equals("user.language")) return; // Locale
                throw new AccessControlException(perm.getClass() + " - " + perm.getName() + ": " + perm.getActions(), perm);
            }
            return;
        }
        throw new AccessControlException(perm.getClass() + " - " + perm.getName() + ": " + perm.getActions(), perm);
    }
}
