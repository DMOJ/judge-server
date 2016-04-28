#pragma once
#ifndef id55D2158A_A5E6_452C_A22B648A8DF8108E
#define id55D2158A_A5E6_452C_A22B648A8DF8108E

#include <windows.h>

typedef struct {
    UINT32 u32LoadLibraryW;
    UINT32 u32GetProcAddress;
} INJECTION_PROCESS_X86, *PINJECTION_PROCESS_X86;

typedef struct {
    UINT64 u64LoadLibraryW;
    UINT64 u64GetProcAddress;
} INJECTION_PROCESS_X64, *PINJECTION_PROCESS_X64;

#endif