package ca.dmoj.java;

import sun.reflect.CallerSensitive;
import sun.reflect.Reflection;

import java.io.File;
import java.io.FilePermission;
import java.lang.reflect.ReflectPermission;
import java.security.AccessControlException;
import java.security.Permission;
import java.util.PropertyPermission;
import java.util.logging.LoggingPermission;
import java.lang.reflect.*;
import java.io.IOException;

public class SubmissionSecurityManager extends SecurityManager {
    @Override
    public void checkPermission(Permission perm) {
        StackTraceElement[] stack = Thread.currentThread().getStackTrace();

        // Disable setAccessible(false)
        // This is done before checking anything else because a malicious submission could
        // potentially have somehow modified System.out and overridden the flush() call with malicious code that would
        // be executed as trusted.
        // setAccessible is never used in JavaSafeExecutor, so it is prudent to put it behind this check as well.
        // Likewise, disable createClassLoader for null packages to a void a definition of "ca.dmoj.java.JavaSafeExecutor" being
        // malicious.
        if (perm instanceof ReflectPermission || (perm instanceof RuntimePermission && perm.getName().equals("createClassLoader"))) {
            Class caller = getCallerClass();
            if (caller.getPackage() == null)
                throw new AccessControlException("fail access to " + perm + " for " + caller);
        }

        if (Thread.currentThread() == JavaSafeExecutor.selfThread || Thread.currentThread() == JavaSafeExecutor.shockerThread)
            return;

        // We have to allow all permissions to printStateAndExit, since it may be called through a proxied
        // System.exit call
        for (StackTraceElement ste : stack) {
            if (ste.getClassName().equals("ca.dmoj.java.JavaSafeExecutor") && ste.getMethodName().equals("printStateAndExit"))
                return;
        }

        String fname = perm.getName().replace("\\", "/");
        if (perm instanceof LoggingPermission) return;
        if (perm instanceof FilePermission) {
            if (perm.getActions().equals("read") &&
                    (fname.endsWith(".class") ||
                            fname.startsWith("/usr/lib/jvm/") ||
                            fname.contains("/jre/lib/zi/")
                    )) // Date
                return;
            if (perm.getActions().equals("read") &&
                    (fname.toLowerCase().endsWith("/ext/nashorn.jar") ||
                            fname.toLowerCase().endsWith("/ext/rhino.jar") ||
                            fname.toLowerCase().endsWith("/jre/lib/content-types.properties")))
                return; // JS
        }
        if (perm instanceof RuntimePermission) {
            if (fname.contains("exitVM")) {
                // Invoke an exit - this will actually call back into this method very soon, but we have a special case
                // set out for this method
                try {
                    JavaSafeExecutor.printStateAndExit();
                } catch (IOException ignored) {
                    ignored.printStackTrace();
                }
                return;
            }
            if (fname.equals("writeFileDescriptor") ||
                    fname.equals("readFileDescriptor") ||
                    fname.equals("fileSystemProvider") ||
                    fname.equals("getProtectionDomain") ||
                    fname.equals("accessDeclaredMembers") ||
                    fname.equals("shutdownHooks") ||
                    fname.equals("setContextClassLoader") ||
                    fname.equals("createClassLoader") || // This one is scary
                    fname.equals("setFactory"))
                return;
            if (fname.startsWith("accessClassInPackage")) {
                if (fname.contains("sun.util.resources") || fname.contains("sun.reflect"))
                    return;
            }
        }

        // If it's gotten this far it is trusted
        if (perm instanceof ReflectPermission) return;

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

    // Shim for Reflection.getCallerClass that should work on Java 8
    private static Class getCallerClass() {
        StackTraceElement[] stack = Thread.currentThread().getStackTrace();
        for (int i = 3; i < stack.length; i++) {
            StackTraceElement elem = stack[i];
            if (!isValid(stack[i])) continue;
            try {
                return Class.forName(elem.getClassName());
            } catch (ClassNotFoundException e) {
                return null;
            }
        }
        return null;
    }

    // From log4j ReflectionUtil
    private static boolean isValid(StackTraceElement element) {
        // ignore native methods (oftentimes are repeated frames)
        if (element.isNativeMethod()) {
            return false;
        }
        final String cn = element.getClassName();
        // ignore OpenJDK internal classes involved with reflective invocation
        if (cn.startsWith("sun.reflect.")) {
            return false;
        }
        final String mn = element.getMethodName();
        // ignore use of reflection including:
        // Method.invoke
        // InvocationHandler.invoke
        // Constructor.newInstance
        if (cn.startsWith("java.lang.reflect.") && (mn.equals("invoke") || mn.equals("newInstance"))) {
            return false;
        }
        // ignore Class.newInstance
        if (cn.equals("java.lang.Class") && mn.equals("newInstance")) {
            return false;
        }
        // ignore use of Java 1.7+ MethodHandle.invokeFoo() methods
        if (cn.equals("java.lang.invoke.MethodHandle") && mn.startsWith("invoke")) {
            return false;
        }
        // any others?
        return true;
    }
}
