# -*- coding: utf-8 -*-
"""
Created on Sun Dec 25 01:14:35 2016

@author: Jian
"""

import os
from PIL import Image

str1 = 'sidebarleft'
filename1 = '%s_Page_1_trimmed.png' % str1
filename2 = '%s_Page_9_trimmed.png' % str1

dir0 = './'
full_filename1 = os.path.join(dir0,filename1)
full_filename2 = os.path.join(dir0,filename2)

images = map(Image.open, [full_filename1, full_filename2])
widths, heights = zip(*(i.size for i in images))

white_band_height = 5  # add a white band between (a) and (b)
total_height = sum(heights) + white_band_height
max_width = max(widths)

new_im = Image.new('RGB', (max_width, total_height), color='#ffffff') # white background

y_offset = 0
for im in images:
  new_im.paste(im, (0, y_offset))
  y_offset += im.size[1] + white_band_height

new_image_filename = '%s_vert.png' % str1
new_im.save(os.path.join(dir0,new_image_filename))

