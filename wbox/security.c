// cl /GS- security.c /LD /Fedmsec32.dll /link /nodefaultlib /entry:DllMain kernel32.lib /def:security.def
// cl /GS- security.c /LD /Fedmsec64.dll /link /nodefaultlib /entry:DllMain kernel32.lib

#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <versionhelpers.h>
#include <processthreadsapi.h>

typedef BOOL (WINAPI *FnSetProcessMitigationPolicy)(
      _In_  PROCESS_MITIGATION_POLICY MitigationPolicy,
      _In_  PVOID lpBuffer,
      _In_  SIZE_T dwLength);

HMODULE hModule;

void *memset(void *s, int c, size_t n)
{
    char* p = s;
    while (n--) *p++ = c;
    return s;
}

BOOL WINAPI DllMain(HINSTANCE hInstance, DWORD dwReason, LPVOID lpvReserved)
{
    hModule = (HMODULE) hInstance;
    return TRUE;
}

__declspec(dllexport) VOID WINAPI InjectMain()
{
    if (IsWindows8OrGreater()) {
        HMODULE hModule = LoadLibraryExW(L"api-ms-win-core-processthreads-l1-1-1.dll", NULL, LOAD_LIBRARY_SEARCH_DEFAULT_DIRS);
        
        if (hModule) {
            FnSetProcessMitigationPolicy func = (FnSetProcessMitigationPolicy) GetProcAddress(hModule, "SetProcessMitigationPolicy");

            if (func) {
                PROCESS_MITIGATION_SYSTEM_CALL_DISABLE_POLICY pmscdp = {0};
                pmscdp.DisallowWin32kSystemCalls = 1;

                if (!SetProcessMitigationPolicy(ProcessSystemCallDisablePolicy, &pmscdp, sizeof pmscdp) &&
                        GetLastError() != 19) {
                    // Error 19 seems to happen when user32.dll is already loaded.
                    DWORD dwWritten;
                    WriteFile(GetStdHandle(STD_ERROR_HANDLE), "Win32k system calls not disabled\n", 33, &dwWritten, NULL);
                }
            }
            FreeLibrary(hModule);
        }
    }

    SetErrorMode(SEM_FAILCRITICALERRORS | SEM_NOALIGNMENTFAULTEXCEPT |
                 SEM_NOGPFAULTERRORBOX | SEM_NOOPENFILEERRORBOX);
    
    FreeLibraryAndExitThread(hModule, 0);
}
