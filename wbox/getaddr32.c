// cl getaddr32.c /link /nodefaultlib /entry:RawEntryPoint /subsystem:windows kernel32.lib shlwapi.lib

#include <windows.h>
#include <shlwapi.h>
#include "getaddr.h"

DWORD CALLBACK RawEntryPoint(void)
{
    INT64 i64Handle;
    HANDLE hMapping;
    HMODULE hKernel32 = GetModuleHandleW(L"kernel32.dll");
    PINJECTION_PROCESS_X86 ipx86;
    MEMORY_BASIC_INFORMATION mbi;
    
    if (!StrToInt64ExW(GetCommandLineW(), STIF_DEFAULT, &i64Handle))
        ExitProcess(1);
    hMapping = (HANDLE) (INT_PTR) i64Handle;
    ipx86 = (PINJECTION_PROCESS_X86) MapViewOfFile(hMapping, FILE_MAP_WRITE, 0, 0, 0);
    
    if (!ipx86)
        ExitProcess(1);

    if (VirtualQuery(ipx86, &mbi, sizeof(mbi)) < sizeof(mbi) ||
            mbi.State != MEM_COMMIT ||
            mbi.BaseAddress != ipx86 ||
            mbi.RegionSize < sizeof ipx86)
        ExitProcess(1);
    
    ipx86->u32LoadLibraryW = (UINT32) (INT_PTR) GetProcAddress(hKernel32, "LoadLibraryW");
    ipx86->u32GetProcAddress = (UINT32) (INT_PTR) GetProcAddress(hKernel32, "GetProcAddress");
    
    UnmapViewOfFile(ipx86);
    CloseHandle(hMapping);

    ExitProcess(0);
}
