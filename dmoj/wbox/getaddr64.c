// cl getaddr64.c /link /nodefaultlib /entry:RawEntryPoint /subsystem:windows kernel32.lib shlwapi.lib

#include <windows.h>
#include <shlwapi.h>
#include "getaddr.h"

DWORD CALLBACK RawEntryPoint(void)
{
    INT64 i64Handle;
    HANDLE hMapping;
    HMODULE hKernel32 = GetModuleHandleW(L"kernel32.dll");
    PINJECTION_PROCESS_X64 ipx64;
    MEMORY_BASIC_INFORMATION mbi;
    
    if (!StrToInt64ExW(GetCommandLineW(), STIF_DEFAULT, &i64Handle))
        ExitProcess(1);
    hMapping = (HANDLE) (INT_PTR) i64Handle;
    ipx64 = (PINJECTION_PROCESS_X64) MapViewOfFile(hMapping, FILE_MAP_WRITE, 0, 0, 0);
    
    if (!ipx64)
        ExitProcess(1);

    if (VirtualQuery(ipx64, &mbi, sizeof(mbi)) < sizeof(mbi) ||
            mbi.State != MEM_COMMIT ||
            mbi.BaseAddress != ipx64 ||
            mbi.RegionSize < sizeof ipx64)
        ExitProcess(1);
    
    ipx64->u64LoadLibraryW = (UINT64) (INT_PTR) GetProcAddress(hKernel32, "LoadLibraryW");
    ipx64->u64GetProcAddress = (UINT64) (INT_PTR) GetProcAddress(hKernel32, "GetProcAddress");
    
    UnmapViewOfFile(ipx64);
    CloseHandle(hMapping);

    ExitProcess(0);
}
