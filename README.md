## BillMe

*Under Development*

## Installation

Make sure your environment has `conda` installed.

Create virtual environment named `pypet`: `conda create -n pypet python=3.6`

Activate it: `. activate pypet`

Install dependencies: `pip install -r requirements.txt`

`pyppeteer-install` *(if this step fails, see the notes below)*

### Notes

#### Chromium doesn't start

If you are running on a Linux machine and encounter the following runtime error:
`/usr/lib/x86_64-linux-gnu/libnss3.so: version 'NSS_3.22' not found`, 
installing `libnss3`, by running `sudo apt install libnss3` might fix the issue.


python setup.py install

locate Chromium under `/home/$USER/.local/share/pyppeteer/local-chromium`
set permissions `chmod 755 -R $CHROMIUM_DIR`
