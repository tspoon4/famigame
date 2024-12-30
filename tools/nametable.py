#!/usr/bin/env python
# coding: utf-8

# In[10]:


import sys
import json
import argparse
import numpy as np # type: ignore
from typing import Optional


# In[11]:


def __find_layer(document: dict, name: str) -> (Optional[dict], int):
    layer, index = None, -1    
    # Iterate over layers table to find the name
    count = 0
    for item in document["layers"]:        
        if item["name"] == name:
            layer, index = item, count
            break
        count += 1
        
    return layer, index


# In[21]:


def __validate_document(document: dict) -> bool:
    result = True
    # Check tile dimensions
    if document["tilewidth"] != 8 or document["tileheight"] != 8:
        result &= False
        print("Error: Tile dimension is not 8x8")
    # Check layer dimensions and layer type    
    for layer in document["layers"]:
        if layer["type"] != 'tilelayer':
            result &= False
            print("Error: layer is not a tilelayer type")
        if layer["width"] % 32 != 0:
            result &= False
            print("Error: layer width is not a multiple of 32")
        if layer["height"] % 30 != 0:
            result &= False
            print("Error: layer height is not a multiple of 30")
    # Check tileset count is the same as layer count, later assuming 
    if len(document["tilesets"]) != len(document["layers"]):
        result &= False
        print("Error: tilesets count is not the same as layers count")

    return result        


# In[22]:


def export_nametable(document: dict, nametable: str, palettes: str) -> bytes:
    data = list()
    tilesets = document["tilesets"]
    
    nt, ni = __find_layer(document, nametable)
    pt, pi = __find_layer(document, palettes)
    hcount, wcount = nt["height"] // 30, nt["width"] // 32
    
    namearray = np.array(nt["data"]).reshape(hcount, 30, wcount, 32) - tilesets[ni]["firstgid"]
    palettearray = np.array(pt["data"]).reshape(hcount, 30, wcount, 32) - tilesets[pi]["firstgid"]
    namearray = namearray.astype(dtype=np.uint8)
    palettearray = palettearray.astype(dtype=np.uint8)
    
    for y in range(0, hcount):
        for x in range(0, wcount):
            data += namearray[y,:,x,:].flatten().tolist()
            attr = palettearray[y,:,x,:].reshape((15, 2, 16, 2))
            attrmin = attr.min(axis=(1, 3))
            attrmax = attr.max(axis=(1, 3))
            
            if not np.all(np.less(attrmin, 4)):
                print("Warning: layer 'palettes' contains values greated than 3")
            if not np.all(np.equal(attrmin, attrmax)):
                print("Warning: layer 'palettes' doesn't contain similar block values")
                
            a = np.vstack((attrmin, np.zeros(16, dtype=np.uint8))).reshape((8, 2, 8, 2))
            for j in range(0, 8):
                for i in range(0, 8):
                    value = (a[j,1,i,1] << 6) | (a[j,1,i,0] << 4)
                    value |= (a[j,0,i,1] << 2) | a[j,0,i,0]
                    data.append(value)
                
    return bytes(data)


# In[25]:


def export_8_bits(document: dict, layer: str) -> bytes:
    data = list()
    tilesets = document["tilesets"]

    lr, li = __find_layer(document, layer)
    hcount, wcount = lr["height"] // 30, lr["width"] // 32    
    level = np.array(lr["data"]).reshape(hcount, 30, wcount, 32) - tilesets[li]["firstgid"]
    level = level.astype(dtype=np.uint8)
    
    for y in range(0, hcount):
        for x in range(0, wcount):
            data += level[y,:,x,:].flatten().tolist()

    return bytes(data)


# In[26]:


def export_2_bits(document: dict, layer: str) -> bytes:
    data = list()
    tilesets = document["tilesets"]

    lr, li = __find_layer(document, layer)
    hcount, wcount = lr["height"] // 30, lr["width"] // 32    
    level = np.array(lr["data"]).reshape(hcount, 30, wcount, 32) - tilesets[li]["firstgid"]
    level = level.astype(dtype=np.uint8)
    
    for y in range(0, hcount):
        for x in range(0, wcount):
            tile = level[y,:,x,:].reshape((15, 2, 16, 2))            
            if not np.all(np.less(tile, 4)):
                print("Warning: layer contains values greater than 3")
                
            for j in range(0, 15):
                for i in range(0, 16):
                    value = (tile[j,1,i,1] << 6) | (tile[j,1,i,0] << 4)
                    value |= (tile[j,0,i,1] << 2) | tile[j,0,i,0]
                    data.append(value)
                    
    return bytes(data)


# In[27]:


def main(argv: list) -> int:
    result = 0
    parser = argparse.ArgumentParser(description='Famicom pattern table tool')
    parser.add_argument('--input', help='the input filename')
    parser.add_argument('--output', help='the output filename')
    parser.add_argument('--layer', help='the layer name in the data')
    parser.add_argument('--b8', action='store_true', help='export data as 8 bits tables')
    parser.add_argument('--b2', action='store_true', help='export data as 2 bits tables')
    arguments = parser.parse_args()
    
    with open(arguments.input, 'r') as f:
        document = json.load(f)
    
    if arguments.b8:
        data = export_8_bits(document, arguments.layer)
        if len(data) > 0:
            with open(arguments.output, 'wb') as f1:
                f1.write(data)
    elif arguments.b2:
        data = export_2_bits(document, arguments.layer)
        if len(data) > 0:
            with open(arguments.output, 'wb') as f2:
                f2.write(data)
    else:
        data = export_nametable(document, 'nametable', 'palettes')
        if len(data) > 0:
            with open(arguments.output, 'wb') as f3:
                f3.write(data)

    return result


# In[ ]:


if __name__ == '__main__':
    sys.exit(main(sys.argv))

