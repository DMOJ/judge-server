@echo off
pushd %~dp0executors
sn -q -k sgKey.snk
csc -nologo csbox.cs -keyfile:sgKey.snk
popd
