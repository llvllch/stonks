from time import sleep
from random import randrange
import argparse
import PIL
from PIL import Image, ImageDraw, ImageFont,  ImageOps
from sys import path
import sys
from IT8951 import constants
import matplotlib 
matplotlib.use('Agg')
import os, random
import textwrap
import qrcode
import feedparser
import requests
import textwrap
import unicodedata
import re
import logging
import os
import io
import yaml 
import time
import socket
import numpy as np
import matplotlib.pyplot as plt
import currency
import logging
import gpiozero

import decimal
dirname = os.path.dirname(__file__)
configfile = os.path.join(os.path.dirname(os.path.realpath(__file__)),'config.yaml')
picdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'images')
quotesfile = os.path.join(os.path.dirname(os.path.realpath(__file__)),'data/quotes.tsv')
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

def mempool(img, config, font):
    feesurl='https://mempool.space/api/v1/fees/recommended'
    try:
        rawmempoolfees = requests.get(feesurl).json()
        _place_text(img,str(rawmempoolfees['hourFee'])+" sat/vB fee", x_offset=-175, y_offset=-105,fontsize=50,fontstring=font)
        success=True
    except:
        success=False
    return img, success

def stoic(img, config):
    try:
        while True:
            filename = os.path.join(dirname, 'images/aristotle.png')
            imlogo = Image.open(filename)
            resize = 300,300
            imlogo.thumbnail(resize)
            numline = -1
            logging.info("get daily stoic")
            stoicurl='https://stoic-quotes.com/api/quote'
            rawquote = requests.get(stoicurl,headers={'User-agent': 'Chrome'}).json()
            logging.info("got quote")
            sourcestring=rawquote['author']
            quotestring=rawquote['text']
            fontstring = "JosefinSans-Light"
            y_text= -300
            height= 110
            width= 38
            fontsize=70
            img.paste(imlogo,(50, 760))
            img, numline = writewrappedlines(img,quotestring,fontsize,y_text,height, width,fontstring)
            draw = ImageDraw.Draw(img) 
            draw.line((500,880, 948,880), fill=255, width=3)
            _place_text(img,sourcestring,0,430,70,"JosefinSans-Light")
            if numline<7 and numline >0:
                success=True
                break
            else:
                img = Image.new("RGB", (1448, 1072), color = (255, 255, 255) )
    except Exception as e:
        logging.info(e)
        message="Interlude due to a data pull/print problem (Daily Stoic)"
        img = beanaproblem(img, message)
        success=False
        time.sleep(10)
    return img,success


def wordaday(img, config):
    try:
        logging.info("get word a day")
        filename = os.path.join(dirname, 'images/rabbitsq.png')
        imlogo = Image.open(filename)
        resize = 300,300
        imlogo.thumbnail(resize)
        d = feedparser.parse('https://wordsmith.org/awad/rss1.xml')
        wad = d.entries[0].title
        fontstring="Forum-Regular"
        y_text=-300
        height= 110
        width= 27
        fontsize=180
        img.paste(imlogo,(50, 100))
        img, numline=writewrappedlines(img,wad,fontsize,y_text,height, width,fontstring)
        
        wadsummary= d.entries[0].summary
        fontstring="GoudyBookletter1911-Regular"
        y_text= -100
        height= 80
        width= 50
        fontsize=60
        img, numline=writewrappedlines(img,wadsummary,fontsize,y_text,height, width,fontstring)
        success=True
    except Exception as e:
        message="Interlude due to a data pull/print problem (Word a Day)"
        img = beanaproblem(img,message)
        success= False
        time.sleep(10)
    return img, success

def textfilequotes(img, config):
    import pandas as pd
    success=False
    filename = os.path.join(dirname, 'images/rabbitsq.png')
    imlogo = Image.open(filename)
    resize = 300,300
    imlogo.thumbnail(resize)
    img.paste(imlogo,(100, 760))
    # Grab The contents of the quotes file, "quotes.csv"
    data=pd.read_csv(quotesfile, sep='\t')
    logging.info(data.head())
    while True:
        choose=data.sample(replace=True)
        logging.info(choose)
        quote=choose.iat[0,0]
        source=choose.iat[0,1]
        try:
            logging.info("Manual File")
            if  len(source)<=25:
                fontstring = "JosefinSans-Light"
                y_text= -300
                height= 90
                width= 33
                fontsize=80
                img, numline =writewrappedlines(img,quote,fontsize,y_text,height, width,fontstring)
                draw = ImageDraw.Draw(img) 
                draw.line((500,880, 948,880), fill=255, width=3)
    #           _place_text(img, text, x_offset=0, y_offset=0,fontsize=40,fontstring="Forum-Regular"):
                _place_text(img,source,0,430,80,"JosefinSans-Light")
            if numline<7:
                success=True
                break
            else:
                img = Image.new("RGB", (264,176), color = (255, 255, 255) )
        except Exception as e:
            message="Interlude due to a data pull/print problem (Text file)"
            img = beanaproblem(img,message)
            success= False
    return img, success

def jsontoquotestack(jsonquotes,quotestack):
    i=0
    # hardcoded 'quality' parameter, migrate this to config file after testing
    try:
        length= len(jsonquotes['data']['children'])
        scorethresh=50
        while i < length:
            if jsonquotes['data']['children'][i]['data']['score']>scorethresh:
                quotestack.append(str(jsonquotes['data']['children'][i]['data']['title']))
            i+=1
    except:
        logging.info('Reddit Does Not Like You')
    return quotestack

def getallquotes(url):
    # This gets all quotes, not just the first 100
    quotestack = []
    rawquotes = requests.get(url,headers={'User-agent': 'Chrome'}).json()
    quotestack = jsontoquotestack(rawquotes, quotestack)
    after=str(rawquotes['data']['after'])
    while after!='None':
        newquotes = requests.get(url+'&after='+after,headers={'User-agent': 'Chrome'}).json()
        try:
            quotestack = jsontoquotestack(newquotes, quotestack)
            after=str(newquotes['data']['after'])
        except:
            after='None'
        logging.info(after)
        time.sleep(1)
    string="We got " + str(len(quotestack)) + " quotes."
    logging.info(string)
    return quotestack

def redditquotes(img, config):
    try:
        logging.info("get reddit quotes")
        numline=-1
        filename = os.path.join(dirname, 'images/rabbitsq.png')
        imlogo = Image.open(filename)
        resize = 300,300
        imlogo.thumbnail(resize)

        quoteurl = config ['display']['quotesurl']
        quotestack = getallquotes(quoteurl)
    #   Tidy quotes
        i=0
        while i<len(quotestack):
            result = unicodedata.normalize('NFKD', quotestack[i]).encode('ascii', 'ignore')
            quotestack[i]=result.decode()
            i+=1
        quotestack = by_size(quotestack, 240)
        
        while True:
            quote=random.choice (quotestack)
        #   Replace fancypants quotes with vanilla quotes
            quote=re.sub("“", "\"", quote)
            quote=re.sub("”", "\"", quote)
        #   Ignore anything in brackets
            quote=re.sub("\[.*?\]","", quote)
            quote=re.sub("\(.*?\)","", quote)
            print
            string = quote
            count = quote.count("\"")
            logging.info("Count="+str(count))
            if count >= 2:
                logging.info("2 or more quotes - split after last one")
                sub = "\""
                wanted = "\" ~"
                n = count
                quote=nth_repl(quote, sub, wanted, n)
                logging.info(quote)

            else:
                matchObj = re.search(r"(\.)\s(\w+)$",quote)
                if matchObj:
                    quote= re.sub("\.\s*\w+$", " ~ "+matchObj.group(2), quote)
                matchObj = re.search(r"\((\w+)\)$",quote)
                if matchObj:
                    quote= re.sub("\(\w+\)$", matchObj.group(1), quote)
                quote= re.sub("\s+\"\s+", "\"", quote)
                quote= re.sub("\s+-|\s+—|\s+―", "--", quote)


            quote= re.sub("~", "--", quote)
            splitquote = quote.split("--")
            quote = splitquote[0]

            quote = quote.strip()
            quote = quote.strip("\"")
            quote = quote.strip()

            if splitquote[-1]!=splitquote[0] and len(splitquote[-1])<=25:
                img.paste(imlogo,(50, 760))
                fontstring = "JosefinSans-Light"
                y_text= -300
                height= 110
                width= 38
                fontsize=70
                img, numline =writewrappedlines(img,quote,fontsize,y_text,height, width,fontstring)
                source = splitquote[-1]
                source = source.strip()
                source = source.strip("-")
                logging.info(source)
                draw = ImageDraw.Draw(img) 
                draw.line((500,880, 948,880), fill=255, width=3)
    #           _place_text(img, text, x_offset=0, y_offset=0,fontsize=40,fontstring="Forum-Regular"):
                _place_text(img,source,0,430,70,"JosefinSans-Light")
            if numline<7 and numline >0:
                success=True
                break
            else:
                img = Image.new("RGB", (1448, 1072), color = (255, 255, 255) )
    except Exception as e:
        message= "Reddit is a bit rubbish"
        print (e)
        img = beanaproblem(img,message)
        success= False
        time.sleep(10)
    return img, success


def newyorkercartoon(img, config):
    try:
        logging.info("Get a Cartoon")
        d = feedparser.parse('https://www.newyorker.com/feed/cartoons/daily-cartoon')
        caption=d.entries[0].summary
        imagedeets = d.entries[0].media_thumbnail[0]
        imframe = Image.open(requests.get(imagedeets['url'], stream=True).raw)
        resize = 1200,800
        imframe.thumbnail(resize, Image.ANTIALIAS)
        imwidth, imheight = imframe.size
        xvalue= int(1448/2-imwidth/2)
        img.paste(imframe,(xvalue, 75))
        fontstring="Forum-Regular"
        y_text= 370
        height= 50
        width= 50
        fontsize=60
        img, numline=writewrappedlines(img,caption,fontsize,y_text,height, width,fontstring)
        success=True
    except Exception as e:
        message="Interlude due to a data pull/print problem (Cartoon)"
        img = beanaproblem(img,message)
        success= False
        time.sleep(10)
    return img, success

def guardianheadlines(img, config):
    try:
        logging.info("Get the Headlines")
        filenameaudrey = os.path.join(dirname, 'images/rabbitsq.png')
        imlogoaud = Image.open(filenameaudrey)
        resize = 300,300
        #imlogoaud.thumbnail(resize)
        if 'headlines' in config:
            d = feedparser.parse(config['headlines']['feedurl'])
            logourl = d['feed']['image']['href']
            imgstream = requests.get(logourl, stream=True)
            imlogo = Image.open(io.BytesIO(imgstream.content))
            # put white background onto logo
            logowidth = imlogo.size[0]
            logoheight = imlogo.size[1]
            imlogo=imlogo.convert('RGBA')
            new_image = Image.new("RGBA", (logowidth,logoheight), "WHITE")
            new_image.paste(imlogo, (0, 0), imlogo)
            imlogo=new_image 
            logging.info('got headline from source')
        else:
            d = feedparser.parse('https://www.theguardian.com/uk/rss')
            filename = os.path.join(dirname, 'images/guardianlogo.jpg')
            imlogo = Image.open(filename)
        resize = 800,150
        imlogo.thumbnail(resize)
        img.paste(imlogo,(70, 50))
        #img.paste(imlogoaud,(100, 760))
        text=d.entries[0].title
        fontstring="Merriweather-Light"
        y_text=-230
        height= 120
        width= 27
        fontsize=70
        img, numlines=writewrappedlines(img,text,fontsize,y_text,height, width,fontstring)
        urlstring=d.entries[0].link
        qr = qrcode.QRCode(version=1,error_correction=qrcode.constants.ERROR_CORRECT_L,box_size=3,border=1,)
        qr.add_data(urlstring)
        qr.make(fit=True)
        theqr = qr.make_image(fill_color="#FFFFFF", back_color="#000000")
        MAX_SIZE=(130,130)
        theqr.thumbnail(MAX_SIZE)
        img.paste(theqr, (1200,870))
        success=True
    except Exception as e:
        message="Interlude due to a data pull/print problem (Headlines)"
        img = beanaproblem(img,message)
        success= False
        time.sleep(10)
    return img, success

def crypto(img, config):
    """  
    The steps required for a full update of the display
    Earlier versions of the code didn't grab new data for some operations
    but the e-Paper is too slow to bother the coingecko API 
    """
    try:
        logging.info("FULL UPDATE")
        allprices, volumes=getData(config)
        # generate sparkline
        logging.info("SPARKLINES")
        limitbool=bool(len(currencystringtolist(config['ticker']['currency']))<=3)
        makeSpark(allprices,limitbool)
        logging.info("NOW DISPLAY")
        # update display
        pic=updateDisplay(img,config, allprices, volumes)
        time.sleep(.2)
        success=True
    except Exception as e:
        message="Interlude due to a data pull/print problem (Crypto)"
        pic = beanaproblem(img,str(e))
        success= False
        time.sleep(10)
    return pic, success

#   The funtions below are all helper stuff for the display functions above
#
#
#

def human_format(num):
    num = float('{:.3g}'.format(num))
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    return '{}{}'.format('{:f}'.format(num).rstrip('0').rstrip('.'), ['', 'K', 'M', 'B', 'T'][magnitude])

def internet(hostname="google.com"):
    try:
        # see if we can resolve the host name -- tells us if there is
        # a DNS listening
        host = socket.gethostbyname(hostname)
        # connect to the host -- tells us if the host is actually
        # reachable
        s = socket.create_connection((host, 80), 2)
        s.close()
        return True
    except:
        logging.info("Google says No")
        time.sleep(1)
    return False


def print_system_info(display):
    epd = display.epd

    print('System info:')
    print('  display size: {}x{}'.format(epd.width, epd.height))
    print('  img buffer address: {:X}'.format(epd.img_buf_address))
    print('  firmware version: {}'.format(epd.firmware_version))
    print('  LUT version: {}'.format(epd.lut_version))
    print()


def clear_display(display):
    logging.info('Clearing display...')
    display.clear()

def beanaproblem(image,message):
#   A visual cue that there was an issue on the last update
    thealert = Image.open(os.path.join(picdir,'arrow.png'))
#   Migrating from the rather dramatic issue screen to drawing attention to the last
#   update time. The persistent display takes care of the rest.
    image.paste(thealert, (10,20))
    logging.info(str("Error message: " + message))
#   Message as QR code to improve error diagnosis
    return image

def getgecko(url):
    try:
        geckojson=requests.get(url, headers=headers).json()
        connectfail=False
    except requests.exceptions.RequestException as e:
        logging.error("Issue with CoinGecko")
        connectfail=True
        geckojson={}
    return geckojson, connectfail

def getData(config):
    """
    The function to grab the data
    """ 
    sleep_time = 10
    num_retries = 5
    crypto_list = currencystringtolist(config['ticker']['currency'])
    fiat_list=currencystringtolist(config['ticker']['fiatcurrency'])
    logging.info("Getting Data")
    days_ago=int(config['ticker']['sparklinedays'])   
    endtime = int(time.time())
    starttime = endtime - 60*60*24*days_ago
    starttimeseconds = starttime
    endtimeseconds = endtime
    allprices = {}
    volumes = {}
    connectbool=False
    for x in range(0, num_retries):  
        # Get the price
        for i in range(len(crypto_list)):
            logging.info("i="+str(i))
            fiat=fiat_list[i]
            whichcoin=crypto_list[i]
            logging.info(whichcoin)
            if config['ticker']['exchange']=='default':
                geckourl = "https://api.coingecko.com/api/v3/coins/markets?vs_currency="+fiat+"&ids="+whichcoin
                rawlivecoin, connectfail = getgecko(geckourl)
                liveprice = rawlivecoin[0]
                pricenow= float(liveprice['current_price'])
                volumenow = float(liveprice['total_volume'])
            else: 
                geckourl= "https://api.coingecko.com/api/v3/exchanges/"+config['ticker']['exchange']+"/tickers?coin_ids="+whichcoin+"&include_exchange_logo=false"
                rawlivecoin, connectfail = getgecko(geckourl)
                theindex=-1
                upperfiat=fiat.upper()
                for i in range (len(rawlivecoin['tickers'])):
                    target=rawlivecoin['tickers'][i]['target']
                    if target==upperfiat:
                        theindex=i
                        logging.debug("Found "+upperfiat+" at index " + str(i))
        #       if UPPERFIAT is not listed as a target theindex==-1 and it is time to go to sleep
                if  theindex==-1:
                    logging.error("The exchange is not listing in "+upperfiat+". Misconfigured - shutting down script")
                    sys.exit()
                liveprice= rawlivecoin['tickers'][theindex]
                pricenow= float(liveprice['last'])
                volumenow = float(liveprice['volume'])

            logging.info("Got Live Data From CoinGecko")
            geckourlhistorical = "https://api.coingecko.com/api/v3/coins/"+whichcoin+"/market_chart/range?vs_currency="+fiat+"&from="+str(starttimeseconds)+"&to="+str(endtimeseconds)
            time.sleep(3) # a little polite pause to avoid upsetting coingecko
           
            rawtimeseries, connectfail = getgecko(geckourlhistorical)
            timeseriesarray = rawtimeseries['prices']
            timeseriesstack = []
            length=len (timeseriesarray)
            i=0
            while i < length:
                timeseriesstack.append(float (timeseriesarray[i][1]))
                i+=1
            timeseriesstack.append(pricenow)
            allprices[str(whichcoin+fiat)] = timeseriesstack
            logging.info(str("Crypto fiat combo: "+whichcoin+fiat))
            volstring=str(str(whichcoin+fiat)+"volume")
            volumes[volstring]=volumenow
            time.sleep(3)

        if connectfail==True:
            message="Trying again in ", sleep_time, " seconds"
            logging.info(message)
            time.sleep(sleep_time)  # wait before trying to fetch the data again
            sleep_time *= 2  # Implement your backoff algorithm here i.e. exponential backoff
        else:
            connectbool=False
            break
    if connectbool==True:
        raise ValueError ('Goingecko did not return data five times in a row')
    return allprices, volumes

def makeSpark(allprices,maximalbool):
    # Draw and save the sparkline that represents historical data

    # Subtract the mean from the sparkline to make the mean appear on the plot (it's really the x axis)    
    logging.info("Update Sparkline graphs")    
    for key in allprices.keys():   
        logging.info(key)    
        x = allprices[key]-np.mean(allprices[key])        # Transform the prices (subtract mean)

        fig, ax = plt.subplots(1,1,figsize=(10,3.3))        # Choose the aspect ratio of each individual plot
        plt.plot(x, color='k', linewidth=3)               # Draw the transformed sparkline
        maxvalue= max(x)
        maxindex= int(np.argmax(x,axis=0))
        minvalue= min(x)
        minindex= int(np.argmin(x,axis=0))

        # Remove the Y axis
        for k,v in ax.spines.items():                     # No Y axis, and x will show as mean because of transformation
            v.set_visible(False)
        ax.set_xticks([])                                 # No ticks
        ax.set_yticks([])                                 # No ticks
        ax.axhline(c='k', linewidth=2, linestyle=(0, (5, 2, 1, 2)))

        if maximalbool:
            plt.plot(maxvalue,  marker="v",c="gray",markersize=25)
            plt.plot(minvalue,  marker="^",c="gray",markersize=25)

        # Save the resulting bmp file to the images directory

        plt.savefig(os.path.join(picdir, key+'spark.png'), dpi=72)
        plt.close('all') # Close plot to prevent memory error
    return


def updateDisplay(image,config,allprices, volumes):
    """   
    Takes the price data, the desired coin/fiat combo along with the config info for formatting
    if config is re-written following adjustment we could avoid passing the last two arguments as
    they will just be the first two items of their string in config 
    """
    crypto_list = currencystringtolist(config['ticker']['currency'])
    fiat_list=currencystringtolist(config['ticker']['fiatcurrency'])
    if 'bold' in config['display'] and config['display']['bold']:
        fontprice= "JosefinSans-Medium"
        fontvolume= "Roboto-Bold"
    else:
        fontprice= "JosefinSans-Light"
        fontvolume= "Roboto-Light"
    days_ago=int(config['ticker']['sparklinedays'])   
    # scaling=3/(config['ticker']['coinsperpage'])
    if len(crypto_list) > 1:
        scaling=3/len(crypto_list)
    else:
        scaling=1
    height=int(150*scaling)
    heightincrement=int(295*scaling)
    index=0
    for key in allprices.keys():
        logging.info(str("Price: "+ key))
        pricenow = allprices[key][-1]  
        fiat=fiat_list[index]
        if fiat=="jpy":
            symbolstring="¥"
        else:
            symbolstring=currency.symbol(fiat.upper())
        whichcoin=crypto_list[index]        
        logging.info(whichcoin)
        if config['display']['inverted'] == True:
            currencythumbnail= 'currency/'+whichcoin+'INV.png'
        else:
            currencythumbnail= 'currency/'+whichcoin+'.png'
        tokenfilename = os.path.join(picdir,currencythumbnail)
        sparkpng = Image.open(os.path.join(picdir,key+'spark.png'))
    #   Check for token image, if there isn't one, get on off coingecko, resize it and pop it on a white background
        if os.path.isfile(tokenfilename):
            logging.info("Getting token Image from Image directory")
            tokenimage = Image.open(tokenfilename)
        else:
            logging.info("Getting token Image from Coingecko")
            tokenimageurl = "https://api.coingecko.com/api/v3/coins/"+whichcoin+"?tickers=false&market_data=false&community_data=false&developer_data=false&sparkline=false"
            rawimage = requests.get(tokenimageurl).json()
            tokenimage = Image.open(requests.get(rawimage['image']['large'], stream=True).raw)
            tokenimage = tokenimage.convert("RGBA")
            if config['display']['inverted'] == True:
                #PIL doesnt like to invert binary images, so convert to RGB, invert and then convert back to RGBA
                tokenimage = ImageOps.invert( tokenimage.convert('RGB') )
                tokenimage = tokenimage.convert('RGBA')
            new_image = Image.new("RGBA", (290,290), "WHITE") # Create a white rgba background with a 10 pixel border
            new_image.paste(tokenimage, (20, 20), tokenimage)   
            tokenimage=new_image
            tokenimage.save(tokenfilename)
        newsize=(200,200)
        tokenimage.thumbnail(newsize,Image.ANTIALIAS)
        pricechange = str("%+d" % round((allprices[key][-1]-allprices[key][0])/allprices[key][-1]*100,2))+"%"
        d = decimal.Decimal(str(pricenow)).as_tuple().exponent
        pricehigh=max(allprices[key])
        pricelow=min(allprices[key])
        if pricenow > 1000:
            pricenowstring =str(format(int(pricenow),","))
            pricehighstring = str(format(int(pricehigh),","))
            pricelowstring = str(format(int(pricelow),","))
        elif pricenow < 1000 and d == -1:
            pricenowstring ="{:.2f}".format(pricenow)
            pricehighstring ="{:.2f}".format(pricehigh)
            pricelowstring ="{:.2f}".format(pricelow)
        elif pricenow<0.1:
            pricenowstring ="{:.3g}".format(pricenow)
            pricehighstring ="{:.3g}".format(pricehigh)
            pricelowstring ="{:.3g}".format(pricelow)
        else:
            pricenowstring ="{:.5g}".format(pricenow)
            pricehighstring ="{:.5g}".format(pricehigh)
            pricelowstring ="{:.5g}".format(pricelow)
        draw = ImageDraw.Draw(image)   
        image.paste(sparkpng, (705,height+40))
        image.paste(tokenimage, (85,height+30))
        text=symbolstring+pricenowstring
        logging.info(symbolstring)
        if len(text)>7:
            pricefontsize=120
        else:
            pricefontsize=130
        volfontsize=50
        _place_text(image, text, x_offset=-175, y_offset=height-420,fontsize=pricefontsize,fontstring=fontprice)
        vol = human_format(volumes[key+"volume"])
        if config['ticker']['exchange']=='default':
            text=pricechange + " vol:" + symbolstring + vol
        else:
            text=pricechange + " vol:" + vol # Currency string omitted as gdax provides volume in coin number
            
        _place_text(image, text, x_offset=-175, y_offset=height-310,fontsize=volfontsize,fontstring=fontvolume)
        if len(crypto_list)<=3:
            _place_text(image, pricelowstring, x_offset=90, y_offset=height-265,fontsize=30,fontstring=fontvolume, justify="l")
            _place_text(image, pricehighstring, x_offset=90, y_offset=height-490,fontsize=30,fontstring=fontvolume, justify="l")
        if 'coinnames' in config['display'] and config['display']['coinnames']:
            _place_text(image, whichcoin, x_offset=-175, y_offset=height-500,fontsize=volfontsize,fontstring=fontvolume)
            logging.info("names")
        height += heightincrement
        index += 1
    text=str(time.strftime("%-I:%M %p, %-d %b %Y"))
    _place_text(image, "Updated: "+text+". "+str(days_ago)+" day data", x_offset=-25, y_offset=-430,fontsize=50,fontstring="JosefinSans-Medium")
    if config['display']['maximalist']==True:
        image, success=mempool(image, config, fontvolume)
        try:
            d = feedparser.parse(config['display']['feedurl'])
            numberofstories=len(d.entries)
            logstring="GOT STORIES, There are:"+str(numberofstories)
            logging.info(logstring)
        except: 
            numberofstories=0
        y_text=45
        height= 100
        width= 37
        fontsize=70
        fontstring=fontprice
        if numberofstories > 1:
            storynum=randrange(numberofstories-1)
            text=d.entries[storynum].title
            image, numline=writewrappedlines(image,text,fontsize,y_text,height, width,fontstring)
            urlstring=d.entries[storynum].link
            qr = qrcode.QRCode(version=1,error_correction=qrcode.constants.ERROR_CORRECT_L,box_size=3,border=1,)
            qr.add_data(urlstring)
            qr.make(fit=True)
            theqr = qr.make_image(fill_color="#FFFFFF", back_color="#000000")
            MAX_SIZE=130
            theqr=theqr.resize([MAX_SIZE,MAX_SIZE])
            image.paste(theqr, (1170,850))
        else:
            text="There is an issue with the news feed"
            image, numline=writewrappedlines(image,text,fontsize,y_text,height, width,fontstring)
        if os.path.isfile('/usr/local/bin/bitcoind'):
            logging.info('looks like a node')
            iconnodemode=True
        else:
            logging.info('not a node')
            iconnodemode=False
        if iconnodemode==True:
            nodeicon = os.path.join(dirname, 'images/noderunner.png')
            nodelogo = Image.open(nodeicon)
            image.paste(nodelogo, (130,800))
    return image


def currencystringtolist(currstring):
    # Takes the string for currencies in the config.yaml file and turns it into a list
    curr_list = currstring.split(",")
    curr_list = [x.strip(' ') for x in curr_list]
    return curr_list

def _place_text(img, text, x_offset=0, y_offset=0,fontsize=40,fontstring="Forum-Regular", justify='c'):
    '''
    Put some centered text at a location on the image.
    '''

    draw = ImageDraw.Draw(img)

    try:
        filename = os.path.join(dirname, './fonts/'+fontstring+'.ttf')
        font = ImageFont.truetype(filename, fontsize)
    except OSError:
        font = ImageFont.truetype('/usr/share/fonts/TTF/DejaVuSans.ttf', fontsize)

    img_width, img_height = img.size
    text_width = font.getlength(text)
    text_height = fontsize
    if justify=="c":
        draw_x = (img_width - text_width)//2 + x_offset
        draw_y = (img_height - text_height)//2 + y_offset
    elif justify=='l':
        draw_x = (img_width)//2 + x_offset
        draw_y = (img_height - text_height)//2 + y_offset
    draw.text((draw_x, draw_y), text, font=font,fill=(0,0,0) )

def writewrappedlines(img,text,fontsize,y_text=0,height=60, width=15,fontstring="Forum-Regular"):
    lines = textwrap.wrap(text, width)
    numoflines=0
    for line in lines:
        _place_text(img, line,0, y_text, fontsize,fontstring)
        y_text += height
        numoflines+=1
    return img, numoflines

def nth_repl(s, sub, repl, n):
    find = s.find(sub)
    # If find is not -1 we have found at least one match for the substring
    i = find != -1
    # loop util we find the nth or we find no match
    while find != -1 and i != n:
        # find + 1 means we start searching from after the last match
        find = s.find(sub, find + 1)
        i += 1
    # If i is equal to n we found nth match so replace
    if i == n:
        return s[:find] + repl + s[find+len(sub):]
    return s

def by_size(words, size):
    return [word for word in words if len(word) <= size]


def display_image_8bpp(display, img, config):

    dims = (display.width, display.height)
    img.thumbnail(dims)
    paste_coords = [dims[i] - img.size[i] for i in (0,1)]  # align image with bottom of display
    # If the config file contains offset coordinates that are nonzero, shift the image by those coordinates 
    # (relative to origin at the bottom left of the screen)
    if 'xshift' in config['display'] and int(config['display']['xshift'])!=0:
        paste_coords[0]=paste_coords[0]-int(config['display']['xshift'])
    if 'yshift' in config['display'] and int(config['display']['yshift'])!=0:
        paste_coords[1]=paste_coords[1]+int(config['display']['yshift'])
    img=img.rotate(180, expand=True)
    if config['display']['inverted']==True:
        img = ImageOps.invert(img)
    display.frame_buf.paste(img, paste_coords)
    display.draw_full(constants.DisplayModes.GC16)
    return

def parse_args():
    p = argparse.ArgumentParser(description='Test EPD functionality')   
    p.add_argument('-v', '--virtual', action='store_true',
                   help='display using a Tkinter window instead of the '
                        'actual e-paper device (for testing without a '
                        'physical device)')
    p.add_argument('-r', '--rotate', default=None, choices=['CW', 'CCW', 'flip'],
                   help='run the tests with the display rotated by the specified value')
    p.add_argument('-e', '--error', action='store_true',
                   help='Brings up the error screen for formatting')

    return p.parse_args()

def currencystringtolist(currstring):
    # Takes the string for currencies in the config.yaml file and turns it into a list
    logging.info(currstring)
    curr_list = currstring.split(",")
    curr_list = [x.strip(' ') for x in curr_list]
    logging.info(curr_list)
    return curr_list

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def listToString(s): 
    
    # initialize an empty string
    str1 = str()

    # Pop the first entry on
    str1=s[0]
    
    # traverse in the string  
    for i in  range(1,len(s)): 
        str1 += ", "+s[i]  
    
    # return string  
    return str1     
        
def togglebutton(display):
    dims = (display.width, display.height)
    img = Image.new("RGB", (1448, 1072), color = (255, 255, 255) )
    img.thumbnail(dims)
    paste_coords = [dims[i] - img.size[i] for i in (0,1)]  # align image with bottom of display
    logging.info("Reset Pressed, initiate shudown")
    filename = os.path.join(dirname, 'images/rabbitsq.png')
    imlogo = Image.open(filename)
    resize = 300,300
    imlogo.thumbnail(resize)
    clear_display(display)
    img.paste(imlogo,(100, 760))
    img=img.rotate(180, expand=True)
    display.frame_buf.paste(img, paste_coords)
    display.draw_full(constants.DisplayModes.GC16)
    os.system('sudo halt')
    return

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def display_startup(display):
    dims = (display.width, display.height)
    img = Image.new("RGB", (1448, 1072), color = (255, 255, 255) )
    img.thumbnail(dims)
    paste_coords = [dims[i] - img.size[i] for i in (0,1)]  # align image with bottom of display
    # set frame buffer to gradient
    ssid=os.popen("sudo iwgetid -r").read()
    filename = os.path.join(dirname, 'images/rabbitsq.png')
    imlogo = Image.open(filename)
    resize = 400,400
    imlogo.thumbnail(resize)
    img = Image.new("RGB", (1448, 1072), color = (255, 255, 255) )
    _place_text(img, 'www.veeb.ch',x_offset=0, y_offset=-350,fontsize=100,fontstring="Roboto-Light")
    _place_text(img, 'Connection: '+ ssid, x_offset=0, y_offset=-240,fontsize=50,fontstring="Roboto-Light")
    _place_text(img, 'IP: '+ get_ip(), x_offset=0, y_offset=-180,fontsize=50,fontstring="Roboto-Light")
    img.paste(imlogo,(100, 600))
    # update display
    img=img.rotate(180, expand=True)
    display.frame_buf.paste(img, paste_coords)
    display.draw_full(constants.DisplayModes.GC16)



def main():
    img = Image.new("RGB", (1448, 1072), color = (255, 255, 255) ) #initialise image
#   If we log to a file, we will need to set up log rotation, so for now it goes to /var/log/syslog
    logging.basicConfig(level=logging.DEBUG)
    args = parse_args()
#   Get the configuration from config.yaml
    with open(configfile) as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    logging.info("Read Config File")
    logging.info(config)
    if not args.virtual:
        from IT8951.display import AutoEPDDisplay

        logging.info('Initializing EPD...')

        # here, spi_hz controls the rate of data transfer to the device, so a higher
        # value means faster display refreshes. the documentation for the IT8951 device
        # says the max is 24 MHz (24000000), but my device seems to still work as high as
        # 80 MHz (80000000)
        display = AutoEPDDisplay(vcom=config['display']['vcom'], rotate=args.rotate, spi_hz=24000000)

        #logging.info('VCOM set to', str(display.epd.get_vcom()))

    else:
        from IT8951.display import VirtualEPDDisplay
        display = VirtualEPDDisplay(dims=(1448, 1072), rotate=args.rotate)

    if not args.error:
        pass
    else:
        img = beanaproblem(display, "This is testing formatting on the page triggered by exceptions.")
        display_image_8bpp(display,img, config)
        exit(0)

    my_list = currencystringtolist(config['function']['mode'])
    weightstring = currencystringtolist(config['function']['weight'])
    weights = [int(i) for i in weightstring]

#   Turn the strings for fiat currency and crypto currency into something we can work with

    curr_string = config['ticker']['currency']
    curr_list = curr_string.split(",")
    curr_list = [x.strip(' ') for x in curr_list]

    fiat_string = config['ticker']['fiatcurrency']
    fiat_list = fiat_string.split(",")
    fiat_list = [x.strip(' ') for x in fiat_list]

    if len(fiat_list)!=len(curr_list):
        logging.info ("Fiat and Crypto lists differ in length. Using first fiat entry only")
        fiat=fiat_list[0]
        fiat_list = [fiat] * len(curr_list)
        config['ticker']['fiatcurrency']=listToString(fiat_list)

    if config['display']['maximalist']==True:
            config['ticker']['currency']=curr_list [0]
    datapulled=False
#   Update frequency sanity check
    if float(config['ticker']['updatefrequency'])<60:
        logging.info("Throttling update frequency to 60 seconds")  
        updatefrequency=60.0
    else:
        updatefrequency=float(config['ticker']['updatefrequency'])
    while internet()==False:
        logging.info("Waiting for Internet")
        time.sleep(1)
    # Set timezone based on ip address
    try:
        os.system("sudo /usr/local/bin/tzupdate")
    except:
        logging.info("Timezone Not Set")
    lastrefresh = time.time()
    # Set up the button
    button = gpiozero.Button(17)
    button.when_pressed = lambda: togglebutton(display) # Note missing brackets, it's a label
    display_startup(display)
    try:
        while True:
            thefunction=random.choices(my_list, weights=weights, k=1)[0]
            numperpage=config['ticker']['coinsperpage']
            if thefunction=="crypto" and len(curr_list)>numperpage and config['display']['maximalist']!=True:                
                chunkslist=list(chunks(curr_list,numperpage))
                fiatlist=list(chunks(fiat_list,numperpage))
                length = len(chunkslist)              
                for i in range(length):
                    imgnew = Image.new("RGB", (1448, 1072), color = (255, 255, 255) )
                    starttime = time.time()
                    configsubset = config
                    configsubset['ticker']['currency']=listToString(chunkslist[i])
                    configsubset['ticker']['fiatcurrency']=listToString(fiatlist[i])                   
                    imgnew, success = eval(thefunction+"(imgnew,configsubset)")
                    if success==True:
                        img= imgnew
                    display_image_8bpp(display,img, config)
                    if success==True:                    
                        lastrefresh=time.time()
                        diff = (lastrefresh - starttime)
                        sleepfor = max(1,updatefrequency-int(diff))
                        sleepstring = str("Got data. Sleeping for: "+str(sleepfor)+" seconds")
                        logging.info(sleepstring)
                        time.sleep(sleepfor)
                    else:
                        sleepfor = 5
                        sleepstring = str("Data Pull Issues. Sleeping for: "+str(sleepfor)+" seconds")
                        time.sleep(sleepfor)
            else:
                starttime = time.time()
                imgnew = Image.new("RGB", (1448, 1072), color = (255, 255, 255) )
                imgnew, success = eval(thefunction+"(imgnew,config)")
                if success==True:
                    img=imgnew
                    display_image_8bpp(display,img, config)
                lastrefresh=time.time()
                if success ==True:
                    diff = (lastrefresh - starttime)
                    # Sleep for update frequency, minus processing time
                    sleepfor = max(1,updatefrequency-int(diff))
                    time.sleep(sleepfor)
                else:
                    time.sleep(5)
    except Exception as e:
        logging.error(e)
        img=beanaproblem(img,str(e)+" Line: "+str(e.__traceback__.tb_lineno))
        display_image_8bpp(display,img,config)  
    except KeyboardInterrupt:    
        logging.info("ctrl + c:")
        img=beanaproblem(img,"Keyboard Interrupt")
        display_image_8bpp(display,img, config)
        exit()


if __name__ == '__main__':
    main()
