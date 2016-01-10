cd %~dp0java_executor
del /s /q objs
rmdir objs
md objs
cd src
javac -source 1.7 -target 1.7 -d ..\objs ca\dmoj\java\*.java
cd ..\objs
del ..\..\executors\java_executor.jar
jar cmf ..\src\META-INF\MANIFEST.MF ..\..\executors\java_executor.jar ca\dmoj\java\*.class
