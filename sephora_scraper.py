from platform import architecture
from requests_html import HTMLSession
s = HTMLSession()
import csv
from bs4 import BeautifulSoup
from selenium import webdriver
import timeit
import time
import requests
import bs4
from rich.console import Console
import shutil
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import urllib.request
console = Console()
import os
import re
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys

lat = 41.91111437719365
long = -87.65268342459851
acc = 100

testProduct = "https://www.sephora.com/product/born-this-way-super-coverage-multi-use-sculpting-concealer-P432298?skuId=2223089"

productList = []

testCSV = "./mini-bath-and-body-links.csv"

def getImage(src, filename, cssSelector, title, variant) :

    imageDriver = webdriver.Chrome()
    imageDriver.get(src)

    productFolder = formatForFileName(title)

    image = imageDriver.find_element(By.CSS_SELECTOR, cssSelector)

    filename = productFolder + "-" + filename
    filename = filename.lower()

    current_directory = os.getcwd()
    final_directory = os.path.join(current_directory, r'{}/{}'.format(productFolder, variant))
    if not os.path.exists(final_directory):
       os.makedirs(final_directory)

    completeName = os.path.join(final_directory, filename)  

    with open(completeName, 'wb') as file:
            file.write(image.screenshot_as_png)
    


    imageHost = 'https://sephora-photos.s3.amazonaws.com/' + filename
    print(imageHost)

    imageDriver.close()


def getAllImages(driver, name, groupName) :

    images = driver.find_elements(By.TAG_NAME, "foreignObject")
    imageCount = 1


    productTitle = driver.find_elements(By.CSS_SELECTOR, "span[data-at='product_name']")
    productTitle = productTitle[0].text

    for image in images :
        n = str(imageCount)
        name = formatForFileName(name)
        if name.__contains__("-Selected") :
            name = name.replace("-Selected", "")

        if groupName == 'none' :
            fileName = name + "-" + n + ".png"
        else :
            fileName = groupName + "-" + name + "-" + n + ".png"

        img = image.find_element(By.TAG_NAME, 'img')
        src = img.get_attribute('src')
        getImage(src, fileName, "img", productTitle, name)
        imageCount += 1


def define_page(url, newFileName):
    driver = webdriver.Chrome()
    driver.get(url)

    productCount = 60
    hasButton = True

    while hasButton :
        try :
            button = driver.find_element_by_xpath("//button[contains(text(), 'Show More Products')]")
            print(productCount)
            button.click()
            time.sleep(2)
            productCount += 60
        except :
            hasButton = False

    soup = BeautifulSoup(driver.page_source, "html.parser")

    skuCount = 0
    # cards = soup.find_all("a")
    cards2 = driver.find_element(By.CLASS_NAME, "css-1322gsb")

    print(cards2)

    cards = cards2.find_elements(By.XPATH, "./*")

    cardCount = 0

    w = open(newFileName, 'w')
    writer = csv.writer(w)

    writer.writerow(["Product Title", "Link"])

    for card in cards :

        try :
            cardCount += 1
            href = card.find_elements(By.TAG_NAME, "a")

            href = href[0].get_attribute('href')

            print("PRODUCT #", cardCount, ": ", href)
            writer.writerow(["", href])
        except :
            href = card.find_elements(By.XPATH, "./*")
            print("PRODUCT #", cardCount, ": " 'no link')
            writer.writerow(['no link',""])

    print(cardCount)


def createCsvFromPages(newFileName, referenceFile, checkDoc, category, subCategory) :

    skuDict = {}

    # cd = open(checkDoc, 'r')
    # checkDocReader = csv.reader(cd)

    # for row in checkDocReader :
    #     if row[0] == 'failure' : continue
    #     skuDict[row[9]] = row

    w = open(newFileName, 'w')
    writer = csv.writer(w)

    r = open(referenceFile, 'r')
    reader = csv.reader(r)

    for row in reader :
        if len(row) < 2 : return
        tryToScrapePage(row, writer, skuDict, category, subCategory)


def getNewInfo(newFileName, referenceFile) :

    w = open(newFileName, 'w')
    writer = csv.writer(w)

    r = open(referenceFile, 'r')
    reader = csv.reader(r)

    for row in reader : 
        print(row)
        if row[1].__contains__('.com') :
            scrapeInfo(row[1], writer)


def scrapeInfo(url, writer) :

    driver = webdriver.Chrome()

    driver.get(url)

    isSeohoraOnlyProduct = checkIfIsSephoraOnly(driver)
    if isSeohoraOnlyProduct : return

    productIsOnlineOnly = checkIfOnlineOnly(driver)
    if productIsOnlineOnly : return

    option1Name = getVariantName(driver, "sku_name_label")
    try : 
        option1Name = option1Name[0].strip()
        if option1Name == 'N' :
            option1Name = False
    except :
        print('no variant')

    try :
        swatchGroup = driver.find_elements(By.TAG_NAME, 'div')
    except :
        print("No swatches")

    if option1Name :
        for swatch in swatchGroup :

            try :
                dataComp = swatch.get_dom_attribute("data-comp")
            except :
                dataComp = False

            if dataComp :

                if dataComp.__contains__("SwatchGroup") :
                    try :
                        buttons = swatch.find_elements_by_tag_name("button")
                        buttons[0].click()
                        
                        ingredients = getProductIngredients(url)
                        howToUse = getHowToUse(url)

                        print("Ingredients: ", ingredients)
                        print("howToUse: ", howToUse)


                    except :
                        'nothing'
    else :
        print("Only one variant")


def noSephoraSheetMaker(newFileName, referenceFile) :

    skuDict = {}

    cd = open(referenceFile, 'r')
    checkDocReader = csv.reader(cd)

    for row in checkDocReader :
        if row[0] == 'failure' : continue
        skuDict[row[9]] = True

    w = open(newFileName, 'w')
    writer = csv.writer(w)

    r = open(referenceFile, 'r')
    reader = csv.reader(r)

    for row in reader :
        if row[13] == "Out of Stock" or row[14] == "Out of Stock" or row[15] == "Out of Stock" or row[16] == "Out of Stock" or row[17] == "Out of Stock" or row[18] == "Out of Stock" :
            row[13] == "Out of Stock"

        if skuDict[row[9]] :
            writer.writerow(row)


def scrapePage(url, writer, category, subcategory, skuDict) :

    row = [""] * 10

    print("URL: ", url)

    driver = webdriver.Chrome()

    driver.get(url)

    isSeohoraOnlyProduct = checkIfIsSephoraOnly(driver)

    if isSeohoraOnlyProduct : return

    # try :
    #     location = getLocation(driver)
    # except :
    #     print("no location")


    # radioDot = driver.find_elements(By.CSS_SELECTOR, "div[class='css-ijij4s']")
    # if len(radioDot) > 2 :
    #     radioDot[2].click()

    # time.sleep(5)

    brandName = getBrandName(driver)

    productIsOnlineOnly = checkIfOnlineOnly(driver)

    if productIsOnlineOnly : return

    option1Name = getVariantName(driver, "sku_name_label")
    try : 
        option1Name = option1Name[0].strip()
        if option1Name == 'N' :
            option1Name = False
    except :
        print('no variant')

    option2Name = getVariantName(driver, "sku_size_label")
    if option2Name :
        option2Name = "Size"

    productName = getProductName(driver)
    print(productName, "PRODUCT NAME")

    try :
        swatchGroup = driver.find_elements(By.TAG_NAME, 'div')
    except :
        print("No swatches")

    hasVariants = False
    isFirstLine = True

    if option1Name :
        for swatch in swatchGroup :

            try :
                dataComp = swatch.get_dom_attribute("data-comp")
            except :
                dataComp = False

            if dataComp :

                if dataComp.__contains__("SwatchGroup") :
                    hasVariants = True
                    try :

                        groupName = swatch.find_elements_by_tag_name("p")
                        groupName = groupName[0].text
                        groupName = formatForFileName(groupName)

                        buttons = swatch.find_elements_by_tag_name("button")
                        clickSwatches(skuDict, writer, url, buttons, driver, groupName, productName, brandName, category, subcategory, isFirstLine, option1Name, option2Name)
                        isFirstLine = False
                    except :
                        'nothing'
    else :
        sku = getSkuId(driver)
        
        try :
            if skuDict[sku] :
                writer.writerow(skuDict[sku])
                console.print("SKU IN DICT", style="red bold")
                return
        except :
            print("Sku not found")
        
        price = getPrice(driver)

        productDescription = getProductDescription(url)

        handle = formatForFileName(productName)
        handle = handle.lower()


        photoFile = "https://sephora-photos.s3.amazonaws.com/" + handle + "-" + handle + "-1" + '.png'
        photoFile = photoFile.lower()

        getAllImages(driver, productName, "none")

        row = writeMainRow(handle, productName, "", "", "", "", brandName, category, subcategory, sku, price, productDescription, photoFile, "")
        writer.writerow(row)


def clickSwatches(skuDict, writer, url, swatches, driver, groupName, productName, brandName, category, subcategory, isFirstLine, option1Name, option2Name = False) :

    isFirstVariant = True

    print(len(swatches))

    for swatch in swatches :

        handle = formatForFileName(productName)
        handle = handle.lower()

        swatchName = swatch.get_dom_attribute('aria-label')
        swatch.click()
        time.sleep(.1)

        sku = getSkuId(driver)

        stock = checkStock(driver)

        firstVariant = getVariantName(driver, "sku_name_label")

        if firstVariant[1].__contains__('-') :
            firstVariant = firstVariant[1].split('-')
            firstVariant = firstVariant[0].strip()
        else :
            firstVariant = firstVariant[1].strip()

        try :
            if skuDict[sku] :
                row = skuDict[sku]
                row.append(stock)

                writer.writerow(row)
                console.print("SKU IN DICT", stock, style="red bold")
                continue
        except :
            print("Sku not found")

        price = getPrice(driver)

        if isFirstVariant and isFirstLine :
            description = getProductDescription(url)

        firstVariant = formatForFileName(firstVariant)

        secondVariant = getVariantName(driver, "sku_size_label")

        if option2Name == False :
            secondVariant = ""
            option2Name = ""
            

        photoFile = "https://sephora-photos.s3.amazonaws.com/" + formatForFileName(productName) + '-' + groupName + "-" + firstVariant + "-1" + '.png'
        photoFile = photoFile.lower()

        print("VARIANT PRICE: ", price)
        print("VARIANT OPTION ONE: ", firstVariant)
        print("VARIANT OPTION TWO: ", option2Name)
        print("PHOTO FILE : ", photoFile.lower())

        if isFirstVariant and isFirstLine :
            row = writeMainRow(handle, productName, option1Name, firstVariant, option2Name, secondVariant, brandName, category, subcategory, sku, price, description, photoFile, stock)
            writer.writerow(row)
        else :
            row = writeVariantRow(handle, firstVariant, secondVariant, brandName, category, subcategory, sku, price, photoFile, stock)
            writer.writerow(row)

        getAllImages(driver, firstVariant, groupName)

        isFirstVariant = False


def getVariantName(driver, dataAtValue) :

    match dataAtValue :

        case "sku_name_label" :

            try :
                variantText = driver.find_element(By.CSS_SELECTOR, "div[data-at='{}'".format(dataAtValue))
                variantText = variantText.find_elements(By.TAG_NAME, "span")
                variantText = variantText[0].text.split(":")    

                return variantText
            except :
                return "No variants"

        case "sku_size_label" :

            try: 
                variantNameContainer = driver.find_element(By.CSS_SELECTOR, "span[data-at='{}'".format(dataAtValue))
                variantText = variantNameContainer.text.replace("Size ", "")

                return variantText
            except :
                return False


def getPrice (driver) :

    priceContainer = driver.find_elements(By.CSS_SELECTOR, "p[data-comp='Price '")
    price = priceContainer[0].find_element(By.TAG_NAME, "b")
    price = price.text

    return price


def formatForFileName(string) :

    filename = re.sub("[^0-9a-zA-Z]+", "-", string)

    lastChar = filename[-1]
    if lastChar == '-' :
        filename = filename[:-1]

    return filename


def getProductName(driver) :

    productTag = driver.find_elements(By.CSS_SELECTOR, "span[data-at='product_name']")
    productName = productTag[0].text
    console.print(productName, style="blue")
    return productName


def getBrandName(driver) :

    brandTag = driver.find_elements(By.CSS_SELECTOR, "a[data-at='brand_name']")
    brandName = brandTag[0].text
    console.print(brandName, style="blue")

    return brandName


def getSkuId(driver) :

    try :
        skuIdContainer = driver.find_elements(By.CSS_SELECTOR, "p[data-at='item_sku']")
        skuId = skuIdContainer[0].text
        skuId = skuId.split(" ")
        skuId = skuId[1]
        print(skuId)

        return skuId
    except :
        return "Not Found"


def getProductDescription(url) :

    try :
        newDriver = webdriver.Chrome()
        newDriver.get(url)

        showMore = newDriver.find_element(By.CLASS_NAME, "css-5fs8cb")
        showMore.click()

        description = BeautifulSoup(newDriver.page_source, "html.parser")

        description = description.find("div", {"class" : "css-u2scbn eanm77i0"})
        description = description.findChildren('div')
        description = description[0]

        newDriver.close()

        print(description)

        return description
    except :
        return "Could not find Description"


def getProductIngredients(url) :
    try :
        newDriver = webdriver.Chrome()
        newDriver.get(url)

        ingredients = newDriver.find_element(By.CSS_SELECTOR, 'button[data-at="ingredients"]')
        ingredients.click()

        Ingredients = BeautifulSoup(newDriver.page_source, "html.parser")
        Ingredients = Ingredients.find("div", {"class" : "css-1ue8dmw eanm77i0"})
        Ingredients = Ingredients.findChildren('div')
        Ingredients = Ingredients[0]
        newDriver.close()

        return Ingredients
    except :
        return "Could not find Description" 


def getHowToUse(url) :
    try :
        newDriver = webdriver.Chrome()
        newDriver.get(url)

        ingredients = newDriver.find_element(By.CSS_SELECTOR, 'button[data-at="how_to_use_btn"]')
        ingredients.click()

        Ingredients = BeautifulSoup(newDriver.page_source, "html.parser")
        Ingredients = Ingredients.find_all("div", {"class" : "css-1ue8dmw eanm77i0"})
        Ingredients = Ingredients[1].findChildren('div')
        Ingredients = Ingredients[0]

        newDriver.close()

        return Ingredients
    except :
        return "NA" 


def checkIfOnlineOnly(driver) :

    container = driver.find_element(By.CSS_SELECTOR, "div[data-comp='PurchaseTypeSection StyledComponent BaseComponent '")
    divs = container.find_elements(By.TAG_NAME, "div")

    isOnlineOnly = False

    for div in divs :
        if div.text.__contains__("Online Only") :
            isOnlineOnly = True
            print("IS ONLINE ONLY")

    return isOnlineOnly


def writeMainRow(handle, productName, option1Name, option1Value, option2Name, option2Value, brand, category, subcategory, sku, price, description, imageUrl, stockStatus) :

    row = [""] * 15

    row[0] = handle
    row[1] = productName
    row[2] = option1Name
    row[3] = option1Value
    row[4] = option2Name
    row[5] = option2Value
    row[6] = brand
    row[7] = category
    row[8] = subcategory
    row[9] = sku
    row[10] = price
    row[11] = description
    row[12] = imageUrl
    row[13] = stockStatus

    return row


def writeVariantRow(handle, option1Value, option2Value, brand, category, subcategory, sku, price, imageUrl, stockStatus) :

    row = [""] * 15

    row[0] = handle
    row[3] = option1Value
    row[5] = option2Value
    row[7] = category
    row[8] = subcategory
    row[9] = sku
    row[10] = price
    row[12] = imageUrl
    row[13] = stockStatus

    return row


def checkStock(driver) :

    flags = driver.find_element(By.CSS_SELECTOR, "div[data-at='sku_name_label']")
    flags = flags.find_elements(By.TAG_NAME, "span")

    stock = ""

    for flag in flags :
        if flag.text.__contains__("OUT OF STOCK") :
            stock = "Out of Stock"

    return stock


def getLocation(driver) :

    time.sleep(2)

    try:
        element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "stores_drop_trigger"))
        )
    except:
        print("FAILED")
    
    button = driver.find_element(By.ID, "stores_drop_trigger")
    button.click()


    try:
        element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "button[data-at='change_store_btn']"))
        )
    except:
        print("FAILED")

    button = driver.find_element(By.CSS_SELECTOR, "button[data-at='change_store_btn']")
    button.click()

    try:
        element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "currentLocation"))
        )
    except:
        print("FAILED")

    

    locationInput = driver.find_element(By.CSS_SELECTOR, 'input[aria-describedby="location_picker_desc"]').send_keys('60642')

    try:
        element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'button[class="css-s4yv5v'))
        )
    except:
        print("FAILED")

    locationList = driver.find_elements(By.CSS_SELECTOR , 'button[class="css-s4yv5v"]')
    locationList[0].click()

    time.sleep(2)

    radios = driver.find_elements(By.CSS_SELECTOR, 'div[data-at="change_store_found_store"]')

    theRadio = False

    for radio in radios :
        ddArray = radio.find_elements(By.TAG_NAME, "dd")
        thisIsTheDD = False
        for dd in ddArray :
            if dd.text.__contains__("938") :
                theRadio = radio
            print(dd.text)

    theRadio.click()
    print("CLICK")
    time.sleep(2)

    button = driver.find_element(By.CSS_SELECTOR, "button[data-at='change_store_use_this_store_btn']")
    button.click()

    time.sleep(1)

    locationStock = driver.find_element(By.CSS_SELECTOR, 'div[class="css-1ql8zxp eanm77i0"')
    locationStock.click()

    time.sleep(.5)

    errorButton = driver.find_elements(By.CSS_SELECTOR, 'button[aria-label="Continue shopping')

    if len(errorButton) > 0 :
        errorButton[0].click()
        time.sleep(.5)


def checkIfIsSephoraOnly(driver) :

    arrayOfFlags = driver.find_elements(By.CSS_SELECTOR, 'span[class="css-mpba0q eanm77i0"]')

    if len(arrayOfFlags) == 0 : return False

    for flag in arrayOfFlags :
        try :
            print(flag.text)
            if flag.text.__contains__("ONLY AT SEPHORA") : 
                print("Skipping Sephora only product")
                return True
        except :
            print("no text")
    
    return False


def tryToScrapePage(row, writer, skuDict, category, subCategory) :

    attempts = 0
    success = False

    if row[1] != ""  and row[1].__contains__('www'):

        # while attempts < 10 and success == False:
            try :
                scrapePage(row[1], writer, category, subCategory, skuDict)
                success = True
            except :
                # attempts += 1
                print("Failed to scrape page")


getNewInfo("test-info.csv", testCSV)