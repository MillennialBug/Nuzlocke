from PIL import Image
from os import listdir

for file in listdir(r'./pkmn'):
    img = Image.open(f'./pkmn/{file}')
    img = img.convert("RGBA")
    data = img.getdata()

    newData = []
    for pixel in data:
        if pixel[0] == 255 and pixel[1] == 255 and pixel[2] == 255:
            newData.append((255, 255, 255, 0))
        else:
            newData.append(pixel)

    img.putdata(newData)
    img.save(f'./pkmn/{file}', "PNG")
