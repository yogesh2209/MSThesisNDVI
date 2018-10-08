# -*- coding: utf-8 -*-
"""
Created on Mon Dec 26 20:03:24 2016

This script trims the white margins of an image file (such as .PNG, or .JPEG),
and by default adds 20-pixel margins to all four sizes of the border, then
outputs the image.
However, transparency information will be lost during the process.

USAGE: python trimimg.py test.png        # trims then adds 20-pixel margins
       python trimimg.py -10 test.png    # trims then adds 10-pixel margins
       python trimimg.py -10.6 test.png  # trims then adds 10-pixel margins
       python trimimg.py -0 test.png     # trims image only, no additional margins

@author: Jian
"""
import os
import sys
import PIL
import PIL.ImageOps

if len(sys.argv) < 2:
    print "\nUsage: trimimg.py filename1 [filename2 ...] OR\n"
    sys.exit()

# | NOTE: sys.argv returns a list of strings.
# |       sys.argv[0] is "trimimg.py"
# |       sys.argv[1] and the rest of the list are what follows "trimimg.py"

if sys.argv[1][0] == '-':  # if the first input arg does start with '-',
    pad_val_str = sys.argv[1][1:]  # then what follows '-' is the pad value (unit: pixels)
    pad_val = int(pad_val_str)  # convert from string into float
    files = sys.argv[2:]   # then the file list starts from index #2
else:
    files = sys.argv[1:]  # the file list starts from index #1
    pad_val = int(20.0)  # the default pad value is 20 pixels

for filename in files:
    im = PIL.Image.open(filename)  # load image
    im = PIL.ImageOps.invert(im.convert('RGB')) # convert from RGBA to RGB, then invert color

    im2 = im#im.crop(im.getbbox())  # create new image
    im2 = PIL.ImageOps.invert(im2) # invert the color back

    new_img_size = (im2.size[0]+2*pad_val,im2.size[1]+2*pad_val) # add padded borders
    im3 = PIL.Image.new('RGB',new_img_size,color=(100,100,100)) # creates new image (background color = white)
    im3.paste(im2,box=(pad_val,pad_val))  # box defines the upper-left corner

    filename_without_ext, file_extension = os.path.splitext(filename)
    new_filename = '%s_trimmed%s' % (filename_without_ext, file_extension)
    im3.save(new_filename)

    print '  %s' % new_filename