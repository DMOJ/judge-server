from dmoj.executors import load_executors
from dmoj.judgeenv import load_env


def main():
    load_env(cli=True)
    load_executors()


if __name__ == '__main__':
    main()
