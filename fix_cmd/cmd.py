import argparse

import fix_cmd


# program options
def get_arguments_parser():
    arguments_parser = argparse.ArgumentParser(description=fix_cmd.__doc__)
    arguments_parser.add_argument(
        '-v', '--version', action='version', version='%(prog)s ' + fix_cmd.__version__)

    return arguments_parser


def main():
    get_arguments_parser().parse_args()


if __name__ == '__main__':
    main()
