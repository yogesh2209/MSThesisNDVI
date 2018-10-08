# -*- coding: utf-8 -*-
"""
Created on Sun Dec 25 01:14:35 2016
@author: Jian
"""

import os
from PIL import Image

str1 = 'minimal'
filename1 = '%s_Page_1_trimmed.png' % str1
filename2 = '%s_Page_9_trimmed.png' % str1

dir0 = './'
full_filename1 = os.path.join(dir0,filename1)
full_filename2 = os.path.join(dir0,filename2)

images = map(Image.open, [full_filename1, full_filename2])
widths, heights = zip(*(i.size for i in images))

white_band_width = 5  # add a white band between (a) and (b)
total_width = sum(widths) + white_band_width
total_height = max(heights)

new_im = Image.new('RGB', (total_width, total_height), color='#ffffff') # white background

x_offset = 0
for im in images:
    new_im.paste(im, (x_offset,0))
    x_offset += im.size[0] + white_band_width

new_image_filename = '%s_TESTESTEST.png' % str1
new_im.save(os.path.join(dir0,new_image_filename))