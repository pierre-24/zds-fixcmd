# ``zds-fixcmd``

[![Build Status](https://travis-ci.org/pierre-24/zds-fixcmd.svg?branch=master)](https://travis-ci.org/pierre-24/zds-fixcmd)

A small project to fix the math expression in ZdS contents due to the change of math processor in [zmarkdown](https://github.com/zestedesavoir/zmarkdown), from [MathJax](https://www.mathjax.org/) to [KaTeX](https://github.com/Khan/KaTeX).

3 fixes are implemented:

+ [fix_newcommand](./zds_fixcmd/fixes/fix_newcommand.py): discover `\newcommand` definitions, and replace the command defined by their value. For example, `\newcommand{\a}[1]{\Delta{#1}}\a{x}` will become `\Delta{x}`.
+ [fix_align](./zds_fixcmd/fixes/fix_align.py): KaTeX only define the `aligned` environment instead of the `align` one, so replace the later by the first one.
+ [fix_spaces](./zds_fixcmd/fixes/fix_spaces.py): trim useless spaces at the begining and end of an expression (which is useful when the new command fix has removed the definitions), but also add a line return at the begining and the end if an environment is present (requirement of the new zmarkdown rather than KaTeX).

All of that runs on on a given container (since `\newcommand` defined in the introduction are still valid until the conclusion of this container), and works by [parsing math expressions](./zds_fixcmd/math_parser.py) (since a regex-based script was more difficult to maintain).

## Installation

### User

With pip:

```bash
pip3 install --user --upgrade git+ssh://git@github.com/pierre-24/zds-fixcmd.git
```

Note that `--user` allow you to install the package without being superuser (see [here](https://pip.pypa.io/en/stable/user_guide/#user-installs>)).
You will probably need to add `$HOME/.local/bin` to `$PATH` for this to work:

```bash
echo 'PATH=$HOME/.local/bin:$PATH' >> ~/.bashrc
```

On the other hand, you can install it in a *virtualenv*.

### Developer

```bash
git clone git@github.com:pierre-24/zds-fixcmd.git

# virtualenv:
virtualenv venv --python=python3
source venv/bin/activate

# dependency
make install-dependencies-dev
python setup.py develop
```
You can run the test suite with `python setup.py test`.

## Usage

The command is `zds-fixcmd`, which takes the `.zip` archive of a content as an input, and output a `.fix.zip` archive, that you can then import back in the website.

## License

[MIT](./LICENSE-MIT) © [Pierre Beaujean](https://pierrebeaujean.net)