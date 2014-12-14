using System;
using System.Collections;
using System.Linq;
using System.Text;
using System.IO;
using System.Security;
using System.Security.Policy;
using System.Security.Permissions;
using System.Reflection;
using System.Runtime.Remoting;

class Sandboxer : MarshalByRefObject {
    static void Main(String[] args) {
        if (args.Length < 2) {
            Console.WriteLine("Usage: sandbox <directory> <assembly> [allowed_files ...]");
            return;
        }

        AppDomainSetup adSetup = new AppDomainSetup();
        adSetup.ApplicationBase = Path.GetFullPath(args[0]);

        PermissionSet permSet = new PermissionSet(PermissionState.None);
        permSet.AddPermission(new SecurityPermission(SecurityPermissionFlag.Execution));
        permSet.AddPermission(new ReflectionPermission(ReflectionPermissionFlag.RestrictedMemberAccess));
        permSet.AddPermission(new FileIOPermission(FileIOPermissionAccess.Read | FileIOPermissionAccess.PathDiscovery, Path.GetFullPath(args[1])));

        for (int i = 2; i < args.Length; ++i)
            permSet.AddPermission(new FileIOPermission(FileIOPermissionAccess.Read | FileIOPermissionAccess.PathDiscovery, args[i]));

        StrongName fullTrustAssembly = typeof(Sandboxer).Assembly.Evidence.GetHostEvidence<StrongName>();

        AppDomain newDomain = AppDomain.CreateDomain("Sandbox", null, adSetup, permSet, fullTrustAssembly);
        ObjectHandle handle = Activator.CreateInstanceFrom(
            newDomain, typeof(Sandboxer).Assembly.ManifestModule.FullyQualifiedName,
            typeof(Sandboxer).FullName
        );
        Sandboxer newDomainInstance = (Sandboxer) handle.Unwrap();
        Environment.Exit(newDomainInstance.ExecuteUntrustedCode(Path.GetFullPath(args[1])));
    }

    public int ExecuteUntrustedCode(string assemblyName) {
        object ret = null;
        try {
            MethodInfo target = Assembly.LoadFrom(assemblyName).EntryPoint;
            ret = target.Invoke(null, target.GetParameters().Length > 0 ?
                                new object[] { new String[0] } : new object[0]);
        } catch (Exception ex) {
            (new PermissionSet(PermissionState.Unrestricted)).Assert();
            Console.WriteLine("E1AE1B1F-C5FE-4335-B642-9446634350A0:\n{0}", ex.ToString());
            CodeAccessPermission.RevertAssert();
        }
        return ret as int? ?? 0;
    }
}
