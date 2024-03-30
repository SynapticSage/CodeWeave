"""
githbu2file is a command line tool to download and output a text 
file representing a given repo or aspects of a given repo.

If user runs `python -m github2file`, 
the first token signals the script to run:

with a 'g2f', it runs github2file.py
else if 'gui' is passed, it runs gui.py
else if 'ts-js-rest' is passed, it runs ts-js-rust2file.py

 all other tokens are passed to the called script
 """

