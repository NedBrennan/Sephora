from PIL import Image

import csv
import os
def fn():       # 1.Get file names from directory
    file_list=os.listdir('./')
    return file_list
    

files = fn()
files.sort()

# print(files)


def cropImage(imageName) :

    im = Image.open("./{}".format(imageName))
 
    width, height = im.size
    
    left = 0
    top = 1
    right = width
    bottom = height
    
    im1 = im.crop((left, top, right, bottom))

    im1.save("./{}".format(imageName))

count = 0
skipped = 0

for file in files :

    try :
        if file.__contains__(".png") :
            count += 1
            cropImage(file)
            print("Progress: ", count, " / ", len(files), skipped)
    except :
        print("Skipped", file)
        count += 1
        skipped += 1
        print("Progress: ", count, " / ", len(files), skipped)