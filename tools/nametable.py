
# coding: utf-8

# In[1]:


import sys
import json
import argparse
import numpy as np # type: ignore
from typing import Optional


# In[ ]:


def __find_layer(document: dict, name: str) -> Optional[dict]:
    layer = None
    for item in document["layers"]:        
        if item["name"] == name:
            layer = item
            break
    return layer


# In[ ]:


def __validate_layer(layer: dict) -> bool:
    result = True
    if layer["type"] != 'tilelayer':
        result &= False
    if layer["width"] % 32 != 0:
        result &= False
    if layer["height"] % 30 != 0:
        result &= False
    
    return result


# In[ ]:


def export_nametable(nametable: dict, palettes: dict) -> bytes:
    assert __validate_layer(nametable)
    assert __validate_layer(palettes)
    assert nametable["height"] == palettes["height"]
    assert nametable["width"] == palettes["width"]
    
    data = list()
    hcount, wcount = nametable["height"] // 30, nametable["width"] // 32
    namearray = np.array(nametable["data"], dtype=np.uint8).reshape(hcount, 30, wcount, 32) - 1
    palettearray = np.array(palettes["data"], dtype=np.uint8).reshape(hcount, 30, wcount, 32) - 1
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


# In[ ]:


def export_8_bits(layer: dict) -> bytes:
    assert __validate_layer(layer)
    
    data = list()
    hcount, wcount = layer["height"] // 30, layer["width"] // 32
    level = np.array(layer["data"], dtype=np.uint8).reshape(hcount, 30, wcount, 32) - 1
    for y in range(0, hcount):
        for x in range(0, wcount):
            data += level[y,:,x,:].flatten().tolist()

    return bytes(data)


# In[ ]:


def export_2_bits(layer: dict) -> bytes:
    assert __validate_layer(layer)
    
    data = list()
    hcount, wcount = layer["height"] // 30, layer["width"] // 32
    level = np.array(layer["data"], dtype=np.uint8).reshape(hcount, 30, wcount, 32) - 1
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


# In[ ]:


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
        layer = __find_layer(document, arguments.layer)        
        if layer:
            data = export_8_bits(layer)
            with open(arguments.output, 'wb') as f1:
                f1.write(data)
        else:
            print("Error: invalid layer name")
            result = -1
    elif arguments.b2:
        layer = __find_layer(document, arguments.layer)        
        if layer:
            data = export_2_bits(layer)
            with open(arguments.output, 'wb') as f2:
                f2.write(data)
        else:
            print("Error: invalid layer name")
            result = -1
    else:
        nametable = __find_layer(document, 'nametable')        
        palettes = __find_layer(document, 'palettes')
        if nametable and palettes:
            data = export_nametable(nametable, palettes)
            with open(arguments.output, 'wb') as f3:
                f3.write(data)
        else:
            print("Error: missing layers 'nametable' or 'palettes'")
            result = -1

    return result


# In[ ]:


if __name__ == '__main__':
    sys.exit(main(sys.argv))

