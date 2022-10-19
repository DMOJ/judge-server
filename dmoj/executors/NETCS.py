from dmoj.cptbox.filesystem_policies import RecursiveDir
from dmoj.executors.compiled_executor import CompiledExecutor

CSPROJ = b"""\
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net6.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
  </PropertyGroup>
</Project>
"""


class Executor(CompiledExecutor):
    ext = 'cs'
    command = 'dotnet'
    test_program = """\
string? line;
while (!string.IsNullOrEmpty(line = Console.ReadLine()))
{
    Console.WriteLine(line);
}"""
    compiler_time_limit = 20
    compiler_write_fs = [
        RecursiveDir('~/.nuget/packages'),
        RecursiveDir('~/.local/share/NuGet'),
        RecursiveDir('/tmp/NuGetScratch'),
    ]

    def create_files(self, problem_id, source_code, *args, **kwargs):
        with open(self._file('Program.cs'), 'wb') as f:
            f.write(source_code)

        with open(self._file('DMOJ.csproj'), 'wb') as f:
            f.write(CSPROJ)

    def get_compile_args(self):
        return [self.get_command(), 'publish', '--configuration', 'release', '--self-contained', 'false']

    def get_compiled_file(self):
        return self._file('bin', 'release', 'net6.0', 'publish', 'DMOJ')
