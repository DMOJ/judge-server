import sys

from dmoj.commands.base_command import Command


class QuitCommand(Command):
    name = 'quit'
    help = 'Exits the DMOJ command-line interface.'

    def execute(self, line: str) -> None:
        sys.exit(0)
