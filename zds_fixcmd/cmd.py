import argparse
import os
import sys

import zds_fixcmd
from zds_fixcmd import content
from zds_fixcmd.fixes import FixableContent, FixError, fix_align, fix_newcommand, fix_spaces

FIXES = [
    fix_newcommand.FixNewCommand(),
    fix_align.FixAlign(),
    fix_spaces.FixSpaces()
]


def exit_failure(msg, status=1):
    """Write a message in stderr and exits

    :param msg: the msg
    :type msg: str
    :param status: exit status (!=0)
    :type status: int
    """

    sys.stderr.write(msg)
    sys.stderr.write('\n')
    return sys.exit(status)


# program options
def get_arguments_parser():
    arguments_parser = argparse.ArgumentParser(description=zds_fixcmd.__doc__)
    arguments_parser.add_argument(
        '-v', '--version', action='version', version='%(prog)s ' + zds_fixcmd.__version__)

    arguments_parser.add_argument('infile', type=str)

    return arguments_parser


def main():
    args = get_arguments_parser().parse_args()

    if not os.path.exists(args.infile):
        return exit_failure('{}: file does not exist')

    try:
        c = FixableContent.extract(args.infile, fixes=FIXES)
    except (content.BadManifestError, content.BadArchiveError) as e:
        return exit_failure('error while opening archive: {}'.format(str(e)))

    try:
        c.fix()
    except FixError as e:
        return exit_failure('error while fixing content: {}'.format(str(e)))

    c.save(args.infile.replace('.zip', '.fix.zip'))


if __name__ == '__main__':
    main()
