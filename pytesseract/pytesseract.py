#!/usr/bin/env python
'''
The original pytesseract along with install instructions can be found
here: https://pypi.python.org/pypi/pytesseract/0.1

LICENSE:
Python-tesseract is released under the GPL v3.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

CONTRIBUTERS:
- Originally written by [Samuel Hoffstaetter](https://github.com/hoffstaetter) 
- [Juarez Bochi](https://github.com/jbochi)
- [Matthias Lee](https://github.com/madmaze)
- [Lars Kistner](https://github.com/Sr4l)

CHANGES MADE:
Small change made on line 138 to explicitly use utf-8 encoding (in case 
computer isn't using uft-8 encoding by default)
'''

# CHANGE THIS IF TESSERACT IS NOT IN YOUR PATH, OR IS NAMED DIFFERENTLY
tesseract_cmd = 'tesseract'

try:
    import Image
except ImportError:
    from PIL import Image
import subprocess
import sys
import tempfile
import os
import shlex

__all__ = ['image_to_string']

def run_tesseract(input_filename, output_filename_base, lang=None, boxes=False, config=None):
    '''
    runs the command:
        `tesseract_cmd` `input_filename` `output_filename_base`
    
    returns the exit status of tesseract, as well as tesseract's stderr output

    '''
    command = [tesseract_cmd, input_filename, output_filename_base]
    
    if lang is not None:
        command += ['-l', lang]

    if boxes:
        command += ['batch.nochop', 'makebox']
        
    if config:
        command += shlex.split(config)
    
    proc = subprocess.Popen(command,
            stderr=subprocess.PIPE)
    return (proc.wait(), proc.stderr.read())

def cleanup(filename):
    ''' tries to remove the given filename. Ignores non-existent files '''
    try:
        os.remove(filename)
    except OSError:
        pass

def get_errors(error_string):
    '''
    returns all lines in the error_string that start with the string "error"

    '''

    lines = error_string.splitlines()
    error_lines = tuple(line for line in lines if line.find('Error') >= 0)
    if len(error_lines) > 0:
        return '\n'.join(error_lines)
    else:
        return error_string.strip()

def tempnam():
    ''' returns a temporary file-name '''
    tmpfile = tempfile.NamedTemporaryFile(prefix="tess_")
    return tmpfile.name

class TesseractError(Exception):
    def __init__(self, status, message):
        self.status = status
        self.message = message
        self.args = (status, message)

def image_to_string(image, lang=None, boxes=False, config=None):
    '''
    Runs tesseract on the specified image. First, the image is written to disk,
    and then the tesseract command is run on the image. Resseract's result is
    read, and the temporary files are erased.
    
    also supports boxes and config.
    
    if boxes=True
        "batch.nochop makebox" gets added to the tesseract call
    if config is set, the config gets appended to the command.
        ex: config="-psm 6"

    '''

    if len(image.split()) == 4:
        # In case we have 4 channels, lets discard the Alpha.
        # Kind of a hack, should fix in the future some time.
        r, g, b, a = image.split()
        image = Image.merge("RGB", (r, g, b))
    
    input_file_name = '%s.bmp' % tempnam()
    output_file_name_base = tempnam()
    if not boxes:
        output_file_name = '%s.txt' % output_file_name_base
    else:
        output_file_name = '%s.box' % output_file_name_base
    try:
        image.save(input_file_name)
        status, error_string = run_tesseract(input_file_name,
                                             output_file_name_base,
                                             lang=lang,
                                             boxes=boxes,
                                             config=config)
        if status:
            errors = get_errors(error_string)
            raise TesseractError(status, errors)
        f = open(output_file_name, "r", encoding="utf-8")
        try:
            return f.read().strip()
        finally:
            f.close()
    finally:
        cleanup(input_file_name)
        cleanup(output_file_name)

def main():
    if len(sys.argv) == 2:
        filename = sys.argv[1]
        try:
            image = Image.open(filename)
            if len(image.split()) == 4:
                # In case we have 4 channels, lets discard the Alpha.
                # Kind of a hack, should fix in the future some time.
                r, g, b, a = image.split()
                image = Image.merge("RGB", (r, g, b))
        except IOError:
            sys.stderr.write('ERROR: Could not open file "%s"\n' % filename)
            exit(1)
        print(image_to_string(image))
    elif len(sys.argv) == 4 and sys.argv[1] == '-l':
        lang = sys.argv[2]
        filename = sys.argv[3]
        try:
            image = Image.open(filename)
        except IOError:
            sys.stderr.write('ERROR: Could not open file "%s"\n' % filename)
            exit(1)
        print(image_to_string(image, lang=lang))
    else:
        sys.stderr.write('Usage: python tesseract.py [-l language] input_file\n')
        exit(2)

if __name__ == '__main__':
    main()
