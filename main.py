from pytesseract import image_to_string
from PIL import Image, ImageEnhance, ImageFilter, ImageGrab
from tempfile import TemporaryFile
import re, numpy, time
import os, sys

# Returns a cropped and binarized image
def enhance(img, name = ""):
    img = crop(img) # Crop image

    # Converts to a jpg and then binarizes it
    with TemporaryFile() as jpgimg:
        img.save(jpgimg, "JPEG")
        img = Image.open(jpgimg)
        img = binarize_image(jpgimg) # Binarize image

    # Converts back to a jpg image object. Saves to a file if in TESTING mode
    if (TESTING):
        jpgimg = open("img/test-output/%s.jpg" % (name), "w+b")
    else:
        jpgimg = TemporaryFile()
    img.save(jpgimg, "JPEG")

    return Image.open(jpgimg)

def binarize_image(filename, threshold = 90):
    imagefile = Image.open(filename)
    img = imagefile.convert('L')  # convert img to monochrome
    img = numpy.array(img)
    img = binarize_array(img, threshold)

    return Image.fromarray(img)

def binarize_array(numpy_array, threshold):
    for i in range(len(numpy_array)):
        for j in range(len(numpy_array[0])):
            if numpy_array[i][j] > threshold:
                numpy_array[i][j] = 255
            else:
                numpy_array[i][j] = 0

    return numpy_array

def crop(img):
    x = img.size[0]
    y = img.size[1]

    # Pre-calculated ratio values of the afk check area
    left = 0.3635
    upper = 0.4426
    right = 0.6359
    lower = 0.5630

    return img.crop((left*x, upper*y, right*x, lower*y))

# Prints in an printf style. Only prints if in DEBUG mode
def dprint(s = "", *args):
    if (DEBUG):
        if (len(args) > 0):
            print(s % args)
        else:
            print(s)

# Returns character for afk check
def find_afk_check(text):
    match = re.search(r'Press[ \t]+(\w)[ \t]+to[ \t]+continue[ \t]+playing.?', text, re.I)

    if match:
        dprint("{} with char '{}'".format(match.group(0), match.group(1)))
        return match.group(1)
    else:
        # If it fails the first time try again with a more lenient regex
        match = re.search(r'[^ \t\n]+[ \t]+([^ \t\n])[ \t]+[^ \t\n]+[ \t]+[^ \t\n]+[ \t]+[^ \t\n]+[^ \t\n]?', text, re.I)
        if match:
            dprint("[Warning] First regex failed. Trying:")
            dprint("{} with char '{}'".format(match.group(0), match.group(1)))
            return match.group(1)

    return None

def run_tests():
    imgs = []
    fails = 0
    tests = 0

    for filename in os.listdir("img/tests"):
        t = (Image.open("img/tests/" + filename), filename)
        tests += 1
        imgs.append(t)

    for e in imgs:
        dprint(e)
    print()

    for ele in imgs:
        img = ele[0]

        img = enhance(img, "enhance-" + ele[1][0])
        text = image_to_string(img, lang='eng')
        c = find_afk_check(text) # Gets character for afk check

        ans = ele[1][0] # Answer is in the file name
        if (c == ans):
            print("Test passed")
        else:
            if (c):
                print("[FAILED] Test failed. Got '%s' instead of '%s'." % (c, ans))
            else:
                print("[FAILED] Test failed. Regex did not return any result.")
            fails += 1

    print("Failed %d out of %d times" % (fails, tests))

def main():
    global TESTING
    global DEBUG
    TESTING = False
    DEBUG = False
    in_afk = False # Flag if still in afk check
    img_i = 0
    checkdir = "img/checks/" + time.strftime("%d%m%Y-%H%M%S")

    os.mkdir(checkdir)

    if ('-t' in sys.argv):
        TESTING = True
    if ('-d' in sys.argv):
        DEBUG = True

    if (TESTING):
        run_tests()

    input("Press enter to start\n")

    while(True):
        img = ImageGrab.grab()

        img = enhance(img)
        text = image_to_string(img, lang='eng')
        c = find_afk_check(text)

        if (c):
            if (in_afk and False):
                dprint("[FAILED] Failed on %d", img_i)
                dprint("[Testing] Trying %s", "a")
                # Test other possibilities
            else:
                dprint("[Testing] Fresh test on '%d'", img_i)
                dprint("Got %s", c)

            img = img.save("{}/{}.jpg".format(checkdir, img_i))
            in_afk = True
            img_i += 1
        else:
            if (in_afk):
                in_afk = False
                # clear afk try history

if __name__ == "__main__":
    main();
