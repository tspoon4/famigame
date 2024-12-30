#!/usr/bin/env python
# coding: utf-8

# In[1]:


import sys
import argparse
import numpy as np # type: ignore
from PIL import Image # type: ignore


# In[2]:


def validate_image(image: np.ndarray) -> np.ndarray:
    img = np.rint(np.array(image) / 85.0) * 85.0
    return img.astype(np.uint8)


# In[3]:


def image_to_pattern(image: np.ndarray) -> bytes:
    data = list()
    for j in range(0, 16):
        for i in range(0, 16):
            x, y = i*8, j*8
            tile = image[y:y+8, x:x+8]
            for p in range(0, 8):
                p0 = 0
                for b in range(0, 8):
                    v = tile[p, b] // (255 // 3)
                    p0 |= (v & 0x01) << (7 - b)
                data.append(p0)
            for p in range(0, 8):
                p1 = 0
                for b in range(0, 8):
                    v = tile[p, b] // (255 // 3)
                    p1 |= ((v >> 1) & 0x01) << (7 - b)
                data.append(p1)
                
    return bytes(data)


# In[4]:


def pattern_to_image(pattern: bytes) -> np.ndarray:
    image = np.zeros((16*8, 16*8), dtype=np.uint8)
    for i in range(0, len(pattern) // 16):
        tile = np.zeros((8, 8), dtype=np.uint8)
        for p in range(0, 8):
            p0 = pattern[i*16+p]
            p1 = pattern[i*16+8+p]
            for b in range(0, 8):
                tile[p, b] = (((p1 >> (7 - b)) & 0x01) << 1) | (p0 >> (7 - b) & 0x01)
        x, y = (i % 16) * 8, (i // 16) * 8
        image[y:y+8, x:x+8] = tile * (255 // 3)
    
    return image


# In[5]:


def main(argv: list) -> int:
    result = 0
    parser = argparse.ArgumentParser(description='Famicom pattern table tool')
    parser.add_argument('--input', help='the input filename')
    parser.add_argument('--output', help='the output filename')
    parser.add_argument('--i2p', action='store_true', help='image to pattern')
    parser.add_argument('--p2i', action='store_true', help='pattern to image')    
    arguments = parser.parse_args()
    
    if arguments.i2p:
        img = Image.open(arguments.input)
        if img.mode != 'L':
            img = img.convert(mode='L')
            print('Warning: input file format is not grayscale, automatic conversion...')            
        image = np.asarray(img)
        image = validate_image(image)
        data = image_to_pattern(image)
        with open(arguments.output, 'wb') as f:
            f.write(data)
    elif arguments.p2i:
        with open(arguments.input, 'rb') as f:
            data = f.read()
            image = pattern_to_image(data)
            img = Image.fromarray(image, mode='L')
            img.save(arguments.output, format='PNG')

    return result


# In[ ]:


if __name__ == '__main__':
    sys.exit(main(sys.argv))

