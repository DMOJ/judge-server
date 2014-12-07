#pragma once

#ifndef id_F985B8FE_F38F_459B_815A3C3CD10C3401
#define id_F985B8FE_F38F_459B_815A3C3CD10C3401

#include <windows.h>

HANDLE SearchProcess(HANDLE hProcess, HANDLE hVictim);
HANDLE SearchForJob(HANDLE hProcess, LPWSTR szParentName);

#endif
