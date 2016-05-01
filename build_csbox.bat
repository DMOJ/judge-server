@echo off
pushd %~dp0dmoj\executors
sn -q -k sgKey.snk
csc -nologo csbox.cs -keyfile:sgKey.snk
popd
