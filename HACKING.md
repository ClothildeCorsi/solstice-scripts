# HACKING

This file contains tips for developing and maintaining `solsticepy`. If you just
want to *use* `solsticepy`, see [README](README.md).

## To install from local source code

If you are making changes to the `solsticepy` code and would like to run it,
the best way is to install it properly. By default, as a non-root user,
the packages will be installed in ~/.local. You can also set up a `virtualenv`
and install inside that, if you want more control and reproducibility.

```bash
cd ~/solstice-scripts
pip install .
```

*Note*: if you want to run `solsticepy` using Python3, then use `pip3` above.

## To upload to PyPI

First update the version number in `setup.py`, then

```bash
python3 setup.py sdist bdist_wheel
python3 -m twine upload 
```

This should also work with `python`, but it's probably best to upload a binary distribution for Python3 rather than Python2.

## To build a local copy of the documentation

You will need Sphinx and the `sphinx_rtd_theme` (`pip instal sphinx_rtd_theme`).

```bash
cd ~/solstice-scripts/doc
make html
xdg-open _build/html/index.html
```

## To update the documentation on `readthedocs`

This should happen automatically, every time you commit code to Github.


