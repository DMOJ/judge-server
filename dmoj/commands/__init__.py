from typing import List, Type

from dmoj.commands.base_command import Command, commands, register_command
from dmoj.commands.diff import DifferenceCommand
from dmoj.commands.help import HelpCommand
from dmoj.commands.problems import ListProblemsCommand
from dmoj.commands.quit import QuitCommand
from dmoj.commands.rejudge import RejudgeCommand
from dmoj.commands.resubmit import ResubmitCommand
from dmoj.commands.show import ShowCommand
from dmoj.commands.submissions import ListSubmissionsCommand
from dmoj.commands.submit import SubmitCommand
from dmoj.commands.test import TestCommand

all_commands: List[Type[Command]] = [
    ListProblemsCommand,
    ListSubmissionsCommand,
    SubmitCommand,
    ResubmitCommand,
    RejudgeCommand,
    DifferenceCommand,
    TestCommand,
    ShowCommand,
    HelpCommand,
    QuitCommand,
]
