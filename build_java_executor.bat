@echo off
pushd %cd%
cd %~dp0java_sandbox
del /f /s /q objs > nul
rmdir /s /q objs
md objs
cd src
javac -source 1.7 -target 1.7 -d ..\objs ca\dmoj\java\*.java
cd ..\objs
del ..\..\dmoj\executors\java-sandbox.jar
jar cmf ..\src\META-INF\MANIFEST.MF ..\..\dmoj\executors\java-sandbox.jar ca\dmoj\java\*.class
popd
