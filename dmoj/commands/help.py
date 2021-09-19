from dmoj.commands.base_command import Command, commands


class HelpCommand(Command):
    name = 'help'
    help = 'Prints listing of commands.'

    def execute(self, line: str) -> None:
        print('Run `command -h/--help` for individual command usage.')
        for name, command in commands.items():
            if command == self:
                continue
            print(f'  {name}: {command.help}')
        print()
