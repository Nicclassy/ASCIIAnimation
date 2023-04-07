import os

from game.animators import animators, terminal_output


os.chdir(os.path.realpath(os.path.dirname(__file__)))


@terminal_output
def main():
    animator = next(animators)()
    animator.run()
    while animator.running:
        pass
    main()


if __name__ == "__main__":
    main()
