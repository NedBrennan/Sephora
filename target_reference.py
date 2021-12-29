from requests_html import HTMLSession
s = HTMLSession()
import csv
from bs4 import BeautifulSoup
from selenium import webdriver
import timeit
from selenium.webdriver.common.by import By
import time
import requests
import bs4
from rich.console import Console
import shutil
from selenium.webdriver.common.keys import Keys

console = Console()


lat = 41.92838817677958
long = -87.68499197115906
acc = 100

def get_heroImage(driver, title, imageCount) :
    imageSoup = BeautifulSoup(driver.page_source, "html.parser")
    images = imageSoup.find_all('div', {'class' : 'slideDeckPicture'})

    index = 0

    isHero = True

    while isHero :
        img = images[index].find('img')
        if 'hei=' not in img['src'] :
            index += 1
        else :
            src = img['src']
            cssSelector = "img[src='" + src + "']"
            imageName = title.replace(' ', '-')
            imageName = title.replace('/', '-')
            filename = imageName + '-' + str(imageCount) + 'variant' + '.png'
            get_image(src, filename, cssSelector)
            imageCount += 1
            isHero = False
    
    return filename

def get_allImages(driver, title, imageCount, soup) :
    images = soup.find_all('div', {'class' : 'slideDeckPicture'})
    imageCount = 1    
    for img in images :
        img = img.find('img')
        if 'hei=' in img :
            continue
        else :
            src = img['src']
            cssSelector = "img[src='" + src + "']"
            imageName = title.replace(' ', '-')
            imageName = title.replace('/', '-')
            filename = imageName + '-' + str(imageCount) + '.png'
            get_image(src, filename, cssSelector)
            imageCount += 1
    
        
    return imageCount

def get_geoDriver() :

    geoDriver = webdriver.Chrome()

    geoDriver.execute_cdp_cmd(
        "Browser.grantPermissions",
        {
            "origin": "https://www.target.com/",
            "permissions": ["geolocation"]
        },
    )
    geoDriver.execute_cdp_cmd(
        "Emulation.setGeolocationOverride",
        {
            "latitude": lat,
            "longitude": long,
            "accuracy": 100,
        },
    )

    geoDriver.get('https://www.target.com/')
    time.sleep(.5)
    try :
        locationFinder = geoDriver.find_element_by_id('storeId-utilityNavBtn')
    except :
        geoDriver.close()
        return 'ERROR'
    finally :
        locationFinder = geoDriver.find_element_by_id('storeId-utilityNavBtn')
    locationFinder.click()
    time.sleep(.5)
    element1 = geoDriver.find_element_by_xpath('//button[.//span[contains(text(), "Use my current location")]]')
    element1.click()
    time.sleep(.5)
    element1 = geoDriver.find_elements_by_css_selector('button[data-test="storeId-listItem-setStore"')
    element1[1].click()
    time.sleep(.5)

    return geoDriver

def get_url(search_term):
    template = "https://www.target.com/s?searchTerm={}"
    search_term = search_term.replace('&', '%26')
    search_term = search_term.replace('-', '')
    search_term = search_term.replace(' ', '+')
    return template.format(search_term)

def get_image(src, filename, cssSelector) :
    print('THIS IS THE SRC ->', src)
    # imageDriver = webdriver.Chrome()
    # imageDriver.get(src)
    # imageDriver.maximize_window()

    # image = imageDriver.find_element_by_css_selector(cssSelector)

    # with open(filename, 'wb') as file:
    #         file.write(image.screenshot_as_png)
    
    # imageHost = 'https://target-scraper.s3.amazonaws.com/' + filename
    # print(imageHost)

    # imageDriver.close()

    image_url = src
    
    # Open the url image, set stream to True, this will return the stream content.
    r = requests.get(image_url, stream = True)
    
    # Check if the image was retrieved successfully
    if r.status_code == 200:
        # Set decode_content value to True, otherwise the downloaded image file's size will be zero.
        r.raw.decode_content = True
        
        # Open a local file with wb ( write binary ) permission.
        with open(filename,'wb') as f:
            shutil.copyfileobj(r.raw, f)
            
        print('Image sucessfully Downloaded: ',filename)
    else:
        print('Image Couldn\'t be retreived')

def define_page(title):
    driver = webdriver.Chrome()
    url = get_url(title)
    # print(url)

    driver.get(url)
    time.sleep(1)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    results = []

    # stock = True
    # success = False

    # while stock :
    #     inStock = results[0].find_all('span')
        
    #     for span in inStock :
    #         if(span.text == 'In stock') :
    #             print('IN STOCK SUCCESS')
    #             success = True
    #             stock = False
    #         else :
    #             stock = False
    count = 0

    # TEMPORARY FIX
    if (True) :
        while len(results) == 0 :
            count += 1
            print('page wait count', count)
            results = soup.find_all('li', {'data-test' : 'list-entry-product-card'})


            if(count > 20) :
                driver.close()
                return -1

        driver.close()
        return results
    else :
        driver.close()
        return 'OUT OF STOCK'

def get_row(title, row, variants):

    # response = s.get(url)
    # response.html.render()
    driver = webdriver.Chrome()
    runs = 0
    results = -1

    while (runs < 3 and results == -1) :
        results = define_page(title)
        if (results == 'OUT OF STOCK') :
            row[12] = results
            return row
        runs += 1
        print("RUN # : ", str(runs))
    
    if (runs == 3 and results == -1) : return row
    print('HIT')

    try :
        driver = get_geoDriver()
        if (driver == 'ERROR') :
            driver = get_geoDriver()

    except :
        try :
            driver = get_geoDriver()
        except :
            print("GEO ERROR #1")
            row[12] = "GEO ERROR #1"
            return row

    print('GEO PASS')
    if (driver == 'GEO ERROR') :
        print('GEO ERROR #2')
        row[12] = results
        return row
    print('GEO PASS #2')   

    # Define new page
    link = ''
    for result in results :
        test = result.find_all('a', {'data-test' : 'product-title'})
        if (len(test) > 0) :
            if title in test[0].text :
                if link == '' :
                    link = test[0]['href']
                    print('TEST HREF: ', test[0]['href'])
                    newPage = 'https://www.target.com' + link
    time.sleep(.5)
    if (link == '') :
        link = results[0].find_all('a')
        newPage = 'https://www.target.com' + link[0]['href']

    print('TITLE: ', title)
    print('LINK: ', link)
    driver.get(newPage)

    soup = BeautifulSoup(driver.page_source, "html.parser")

    # WRITE BRAND NAME
    ##################
    shop = driver.find_element_by_xpath('//span[contains(text(), "Shop all")]')
    shop = shop.text.replace('Shop all ', '')
    row[3] = shop
    ##################
    imageNum = 1
    # GET ALL IMAGES FOR PRODUCT
    imageNum = get_allImages(driver, title, imageNum, soup)



    price = False
    priceCount = 0
    variantPrices = {}
    variantImages = {}

    if (variants) :
        print("HAS VARIANTS")
        dropdown = driver.find_elements_by_xpath('//button[contains(@data-test, "SelectVariationSelector")]')
        if (len(dropdown) == 1) :
            count = 1
            for var in variants :
                try :
                    print("VARIANT COUNT: ", count)
                    dropdown = driver.find_elements_by_xpath('//button[contains(@data-test, "SelectVariationSelector")]')
                    time.sleep(.5)
                    dropdown[0].click()
                    time.sleep(.5)
                    xpath = '//a[contains(@aria-label, "' + var + '")]'
                    print("XPATH A TAG: ", xpath)
                    buttonLength = 0
                    attempts = 0
                    while attempts < 5 and buttonLength == 0 :
                        testingVar = driver.find_elements_by_xpath(xpath)
                        buttonLength = len(testingVar)
                        attempts += 1
                        print("attempted button")
                    time.sleep(.5)
                    print(testingVar)
                    count += 1
                    if (len(testingVar) != 0) :
                        testingVar[0].click()
                        time.sleep(.5)
                        priceSoup = BeautifulSoup(driver.page_source, 'html.parser')
                        price = priceSoup.find('div', {'data-test' : 'product-price'})
                        print('VARIANT PRICE: ', price.text)
                        variantPrices[var] = price.text
                        hero = get_heroImage(driver, title, imageNum)
                        variantImages[var] = hero
                        imageNum += 1
                    
                except :
                    print("VARIANT ERROR")
        else :
            for var in variants :
                try :

                    xpath = '//button[contains(@aria-label, "' + var + '")]'
                    print("XPATH BUTTON: ", xpath)
                    
                    testingVar = []
                    buttonLength = 0
                    attempts = 0
                    while attempts < 5 and buttonLength == 0 :
                        testingVar = driver.find_elements_by_xpath(xpath)
                        buttonLength = len(testingVar)
                        attempts += 1
                        print("attempted button")
                        
                    if (len(testingVar) == 1) :

                        testingVar[0].click()
                        time.sleep(.5)
                        priceSoup = BeautifulSoup(driver.page_source, 'html.parser')
                        price = priceSoup.find('div', {'data-test' : 'product-price'})
                        print('VARIANT PRICE: ', price.text)
                        variantPrices[var] = price.text
                        print(variantPrices)
                        hero = get_heroImage(driver, title, imageNum)
                        variantImages[var] = hero
                        imageNum += 1
                except :
                    print("Variant Error")
                

    while(price == False and priceCount < 20) :
        price = soup.find('div', {'data-test' : 'product-price'})
        print(type(price))
        priceCount += 1

    if(price) :
        print("NOT STRING PRICE", price)
        price = price.text
        row[7] = price
    else :
        row[7] = 'NULL'

    results = soup.find_all('h3')   

    for result in results :
        if(result.text == 'Highlights') :
            parent = result.parent
            bullets = parent.find('ul').find_all('li')
            bulletString = '<ul>'

            for bullet in bullets :
                uniqueBullet = "<li>" + bullet.text + "</li>"
                bulletString += uniqueBullet
            row[10] = bulletString + '</ul>'

        if(result.text == 'Description') :
            parent = result.parent
            description = parent.find('div').text
            row[9] = description

            # print(description)
        if(result.text == 'Specifications') :
            parent = result.parent
            items = parent.find_all('b')

            for item in items :
                if(item.text == "UPC") :
                    parent = item.parent
                    upc = parent.text
                    upc = ''.join(filter(str.isdigit, upc))

                    # print(upc)
                    row[8] = upc
    
    brandLink = soup.find('a', {'data-test' : 'shopAllBrandLink'})
    brand = brandLink.find('span')
    brand = brand.text.replace('Shop all ', '')
    
    
    row[3] = brand
    driver.close()
    return row

def write_new_file(newFileName, fileToBeRead) :

    w = open(newFileName, 'w')
        # create the csv writer
    writer = csv.writer(w)

    f = open(fileToBeRead, 'r')

    reader = csv.reader(f)

    count = 0

    f = open(fileToBeRead, 'r')
    reader = csv.reader(f)     
    
    for row in reader :
        if (row[0] != '' and row[0] != 'item name') :
            try :
                row = get_row(row[0], row, False)
                writer.writerow(row)
            except :
                row[12] = 'NO WRITE'
                writer.writerow(row)    

            count += 1
            print("Row " + str(count) + " written.")
        else :
            count += 1
            print("Row " + str(count) + " written.")
            writer.writerow(row)

def write_variants(newFileName, fileToBeRead) :

    w = open(newFileName, 'w')
        # create the csv writer
    writer = csv.writer(w)


    f = open(fileToBeRead, 'r')

    reader = csv.reader(f)

    count = 0

    hasVariants = ''
    variants = {}

    for row in reader :
        if (row[0] != '' and row[0] != 'item name') :
            if (row[2] != '') :
                hasVariants = row[0]
                variants[row[0]] = []
                variants[row[0]].append(row[2])
            else :
                hasVariants = ''
        else :
            if (row[0] == '' and row[2] != '') :
                variants[hasVariants].append(row[2])

    f = open(fileToBeRead, 'r')
    reader = csv.reader(f)     
    
    print(variants)
    currentVariant = {}
    currentVariantPos = 0
    for row in reader :
        if (row[0] != '' and row[0] != 'item name') :
            try :
                row = get_row(row[0], row, variants[row[0]])
                variants[row[0]]
                print('Variant Name From Row: ', row['row'][2])
                print('Variants returned from program: ', row['variants'])
            except :
                row = row  

            try :
                row['row'][7] = row['variants'][row['row'][2]]
                currentVariant = row['variants']      
                row = row['row']
            except :
                currentVariant = {}
                print('PRICE WRITE FAIL MAIN')
            count += 1
            writer.writerow(row)
            print("Row " + str(count) + " written.")
            currentVariantPos += 1
        else :
            print('CURRENT VARIANT: ', currentVariant)
            try :
                price = currentVariant[row[2]]
                row[7] = price
            except :
                print('PRICE WRITE FAILED')
            writer.writerow(row)

write_new_file('601-881-Result.csv', './601-881.csv')