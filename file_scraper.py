import requests
import random
import datetime
import time
import os
import logging
import concurrent.futures
import csv
import urllib.parse
import re
import sys

try:
    import lxml
except:
    pass
try:    
    import html5lib
except:
    pass

import gc
import imghdr
import argparse

from tqdm import tqdm
from bs4 import BeautifulSoup
from pathlib import Path
from torpy.http.requests import TorRequests, tor_requests_session, do_request as requests_request
from torpy.utils import AuthType, recv_all, retry


class AnonStaticWebScraper():
    def __init__(self, args):
        self.HS_BASIC_HOST = os.getenv('HS_BASIC_HOST')
        self.HS_BASIC_AUTH = os.getenv('HS_BASIC_AUTH')
        self.HS_STEALTH_HOST = os.getenv('HS_STEALTH_HOST')
        self.HS_STEALTH_AUTH = os.getenv('HS_STEALTH_AUTH')
        self.auth_data = {self.HS_BASIC_HOST: (self.HS_BASIC_AUTH, AuthType.Basic)}
        print(self.auth_data)

        self.characters = r"\/:?<>|*"#characters that cannot be used in the name of a file

        #scraping_parameter

        self.RETRIES = 1
        self.TIMEOUT = 10

        #Logging
        self.logging_folder = Path('web_img_scraping_log')
        self.logging_folder.mkdir(exist_ok=True)
        logging.getLogger('requests').setLevel(logging.INFO)
        logging.basicConfig(format='[%(asctime)s] [%(threadName)-16s] %(message)s', level=logging.INFO,handlers=[logging.FileHandler("./web_img_scraping_log/debug"+str(time.time())+".log"),logging.StreamHandler(sys.stdout)])
        self.logger = logging.getLogger(__name__)


        #fake-useragent

        self.ua_list = ["Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"]
        print("user-agent number:"+str(len(self.ua_list)))

        self.ISO_lang_code = ["en-US"]
        #ISO_lang_code = ["af","af-ZA","ar","ar-AE","ar-BH","ar-DZ","ar-EG","ar-IQ","ar-JO","ar-KW","ar-LB","ar-LY","ar-MA","ar-OM","ar-QA","ar-SA","ar-SY","ar-TN","ar-YE","az","az-AZ","be","be-BY","bg","bg-BG","bs-BA","ca","ca-ES","cs","cs-CZ","cy","cy-GB","da","da-DK","de","de-AT","de-CH","de-DE","de-LI","de-LU","dv","dv-MV","el","el-GR","en","en-AU","en-BZ","en-CA","en-CB","en-IE","en-JM","en-NZ","en-PH","en-TT","en-US","en-ZA","en-ZW","eo","es","es-AR","es-BO","es-CL","es-CO","es-DO","es-EC","es-ES","es-GT","es-HN","es-MX","es-NI","es-PA","es-PE","es-PR","es-PY","es-SV","es-UY","es-VE","et","et-EE","eu","eu-ES","fa","fa-IR","fi","fi-FI","fo","fo-FO","fr","fr-BE","fr-CA","fr-CH","fr-FR","fr-LU","fr-MC","gl","gl-ES","gu","he","he-IL","hi","hi-IN","hr","hr-BA","hr-HR","hu","hu-HU","hy","hy-AM","id","id-ID","is","is-IS","it","it-CH","it-IT","ja","ja-JP","ka","ka-GE","kk","kk-KZ","kn","kn-IN","ko","ko-KR","kok","kok-IN","ky","ky-KG","lt","lt-LT","mi","mi-NZ","mk","mk-MK","mn","mn-MN","mr","mr-IN","ms","ms-BN","ms-MY","mt","mt-MT","nb","nb-NO","nl","nl-BE","nl-NL","nn-NO","ns","ns-ZA","pa","pa-IN","pl","pl-PL","ps","ps-AR","pt","pt-BR","pt-PT","qu","qu-BO","qu-EC","qu-PE","ro","ro-RO","ru","ru-RU","sa","sa-IN","se","se-FI","se-NO","se-SE","sk","sk-SK","sl","sl-SI","sq","sq-AL","sr-BA","sv","sv-FI","sv-SE","sw","sw-KE","syr","syr-SY","ta","ta-IN","te","te-IN","th","th-TH","tl","tl-PH","tn-ZA","tr","tr-TR","tt","tt-RU","ts","uk","uk-UA","ur","ur-PK","uz","vi","vi-VN","xh","xh-ZA","zh","zh-CN","zh-HK","zh-MO","zh-SG","zh-TW","zu","zu-ZA"]

        #retry connection if statuscode are 500, 501, etc. 

        self.TIMEOUT_COUNT = 4

        #cookie

        self.cookie = {}


    def delay_partern(self, count):
        random_number = random.randint(1,5)
        random_number2 = random.uniform(0.1,10)
        x = random.random()+random.random()+0.001
        time.sleep(random.uniform(count,count+4))
        if random_number == 1:
            time.sleep(random.uniform(0,random_number2))
            random.seed()
        if random_number == 2:
            time.sleep(random.uniform(0,random_number2**(x*0.1)))
        if random_number == 3:
            time.sleep(random.uniform(0,x**(random_number2*0.3)))
            random.seed()
        if random_number == 4:
            time.sleep(random.uniform(0,x**(x*0.1)))
        if random_number == 5:
            time.sleep(random.uniform(0,x*random_number2*0.5))
            random.seed()
        return

    def web_response(self, res):
        logging.info("status code: "+str(res.status_code)+" "+str(res.reason))#show the status code of the website
        logging.info("Redirect: "+str(res.history))#show the number of redirects
        logging.info(str(res.elapsed))
        logging.info("encoding: "+str(res.encoding))
        logging.info("Response Headers: ")
        logging.info(str(res.headers))
        #print(http.client.parse_headers(res))
        return

    def fake_header(self):
        
        Host_name = None
        return {"Host": Host_name,"Connection": "keep-alive","Upgrade-Insecure-Requests": "1","User-Agent": self.ua_list[random.randint(0,len(self.ua_list)-1)],"Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8","Accept-Language":self.ISO_lang_code[random.randint(0,len(self.ISO_lang_code)-1)],"Accept-Encoding": "gzip, deflate, br"}


    def make_folder(self):    
        print("Creating save folder.")
        
        DATE = str(datetime.date.today())
        output_folder = Path('img_'+DATE)
        output_folder.mkdir(exist_ok=True)
        
        TIME = str(time.time())
        output_folder = Path('img_'+DATE+'/'+TIME)
        output_folder.mkdir(exist_ok=True)
        
        print("Save folder creation completed.")
        return './img_'+DATE+'/'+TIME+"/"

    def beautifulsoup_cleansing(self, soup, url):
        linklist2 = []
        linklist2_2 = []
        linklist3 = []
        content = [["img","src"],["a","href"],["img","srcset"]]
        url_parts = url.rsplit("/")    
        
        for i in range(0,len(content)):
            for link in soup.findAll(content[i][0]):#basic1            
                link = link.get(content[i][1])
                
                if link == None:
                    link = ""
                    
                try:
                    if self.only_img_save == False:
                        if not link == "":
                            linklist2.append(link)
                        else:
                            pass
                    else:
                        if ("jpg" in link) or ("png" in link) or ("jpeg" in link) or ("gif" in link) or ("bmp" in link) or ("svg" in link) or ('ico' in link) or ('pdf' in link) or ("JPG" in link) or ("PNG" in link) or ("JPEG" in link) or ("GIF" in link) or ("BMP" in link) or ("SVG" in link) or ('ICO' in link) or ('PDF' in link) and (not link == ""):
                            linklist2.append(link)
                        else:
                            pass                    
                except:
                    pass    
                    
        for image in linklist2:
            if "http://" in url:            
                url_precursor = "http:"
                print("caution! http cannot ensure anonymity.")
            else:
                url_precursor = "https:"
            image2 = "/"+image
            idx = image.find("./")#"./" ("../") is removed to input "/".
            image = image[idx+1:]
            url_list = [image,url_precursor+image,str(url)+r"/"+image,str(url)+image]
            
            for k in range(0,len(url_parts)-2):
                url_precursor = url_precursor +"/"+ url_parts[k+1]
                image3 = str(url_precursor)+str(image)
                image4 = str(url_precursor)+str(image2)            
                url_list.append(image3)
                url_list.append(image4)
                
            for k in url_list:
                if (k.count(r"https:") == 1 or k.count(r"http:") == 1) and k.count(r"///") == 0 and (re.match(r'https:\/\/.+', k) != None or re.match(r'http:\/\/.+', k) != None) and k.count(r"//") == 1:
                    linklist2_2.append(k)
                        
        for i in range(0,len(linklist2_2)):    
            if not linklist2_2[i] in linklist3:
                linklist3.append(urllib.parse.quote(linklist2_2[i], safe=":/ ! = & % ? $ ' ( ) * + , - . ; < > @ [ ] ^ _ `{ | }"))
        
        empty_data_num = (len(linklist3)//100)*self.delay_scraping
        
        
        if self.delay_scraping != 0 and not linklist3 == []:
            for i in range(0,empty_data_num+1):
                linklist3.insert(random.randint(1,len(linklist3)-1),"empty_data")
        
        del linklist2_2

        return linklist3, linklist2


    def tor_requests_and_filesave(self, save_path3,image,header,pbar,html_file_img_name,html_save_path):
        
        pbar.update(1)
        
        self.delay_partern(self.COOL_TIME)
        
        NUM = random.randint(0,1001)
        NUM2 = random.randint(10,1000)
        
        if NUM > NUM2:#randomize the cool time to make bot resemble human.
            self.delay_partern(2)
            random.seed()
        
        logging.info(str(image))
        logging.info("fake user agent："+str(header))
        i = str(time.time())+"_"+str(NUM)
        try:
            for j in range(1,self.TIMEOUT_COUNT):
                self.delay_partern(0)
                
                with tor_requests_session(hops_count=3+self.HOP_COUNT,auth_data=self.auth_data,headers=header, retries=self.RETRIES) as session:#Download image files via Tor.
                    pict = session.get(image.format(self.HS_BASIC_HOST), timeout=1+self.TIMEOUT,stream=True,cookies=self.cookie)
                    
                    self.web_response(pict)
                    
                    image = "".join(x for x in image if x not in self.characters)#Remove unusable characters from file names.
                    if pict.status_code == 200:
                        with open(save_path3 + f'{i}'+"."+image.split('.')[-1],'wb') as f:
                            f.write(pict.content)
                        break
                        
                    elif pict.status_code >= 500:
                        print("time out! connecting again.....")
                        time.sleep(2**j)
                        
                    else:
                        break
                        
        except Exception as e:
            print(e)
            print("\nError\n")
            
        try:
            extention = imghdr.what(save_path3 + f'{i}'+"."+image.split('.')[-1])
            
        except Exception as e:
            print(e)
            print("\nFileNotFoundError\n")
            return

        if extention == None:
            print("It may not be an image file.\n")
             
        else:#Add the exact file name extension of the image file.
            print(save_path3,str(i),"\n")
            os.rename(save_path3 + f'{i}'+"."+image.split('.')[-1],save_path3 + f'{i}'+"."+image.split('.')[-1]+"."+str(extention))#Rename file
        del session
        self.delay_partern(1)
        return



    def html_parse(self, save_path3, url):
        
        header = self.fake_header()

        logging.info("fake user agent："+str(header))
        try:
            with tor_requests_session(hops_count=3+self.HOP_COUNT,auth_data=self.auth_data,headers=header, retries=self.RETRIES) as session:
                html = session.get(url.format(self.HS_BASIC_HOST), timeout=1+self.TIMEOUT,cookies=self.cookie)
                self.web_response(html)
                
                if html.status_code != 200:
                    logging.info("This website is not working. Exit...")
                    html = ""
                    os.rmdir(save_path3)
                    return BeautifulSoup("", 'html.parser'), ""
                    
            try:
                soup = BeautifulSoup(html.content, 'lxml')
            except:
                soup = BeautifulSoup(html.content, 'html5lib')
            logging.info("Retrieved via Tor.")
            
        except Exception as e:
            logging.info(str(e)+"\nUnable to connect with Tor. Exit...")
            os.rmdir(save_path3)
            return BeautifulSoup("", 'html.parser'), ""#Prohibit all but Tor connections.
        html_save_path = save_path3 +str(time.time())+".html"
        with open(html_save_path,'wb') as f:
            f.write(html.content)
            logging.info("Saved the html file of the web site.")  
            
        return soup,html_save_path



    def main_scrape(self, url):

        self.delay_scraping = args.interval
        self.HOP_COUNT = args.node_number
        multi_threaded_parallel_processing = args.threads
        
        if multi_threaded_parallel_processing > 101:
            multi_threaded_parallel_processing = 100
            
        self.COOL_TIME = args.cooltime
        self.only_img_save = args.all
        
        save_path3 = self.make_folder()
        
        print("Getting html from a web site.")
        soup, html_save_path = self.html_parse(save_path3,url)
        
        print("\nExtracts website image links from html.")
        
        linklist3, linklist2 = self.beautifulsoup_cleansing(soup,url)
        
        print("\nDisplays the extracted URL and its fragments.")
        print(linklist3)
        print("the number of url："+str(len(linklist3)))
        
        print("\nStart image extraction\nThe name of the extracted image will be displayed.")
        SILENT_MODE = args.silent_mode
        if SILENT_MODE == False:
            with tqdm(total=len(linklist3)) as pbar:
                with concurrent.futures.ThreadPoolExecutor(max_workers=multi_threaded_parallel_processing) as p:#multi-threaded parallel processing.
                    for i, img in enumerate(linklist3):
                        #Randomize the user agent for each session.
                        for j in linklist2:
                            if j in img:
                                html_file_img_name = j
                        future = p.submit(self.tor_requests_and_filesave,save_path3,img,self.fake_header(),pbar,html_file_img_name,html_save_path)
                        del future
        else:
            
            with tqdm(total=len(linklist3)) as pbar:
                for i, img in enumerate(linklist3):
                    for j in linklist2:
                        if j in img:
                            html_file_img_name = j
                    self.tor_requests_and_filesave(save_path3,img,self.fake_header(),pbar,html_file_img_name,html_save_path)
                    self.delay_partern(1)
                    time.sleep(1)
                    
        logging.info("Completed.")
        
        
        del linklist3, linklist2
        
        return


    def csv_reader(self, csv_file_name):
        URL_LIST = []
        
        with open("./"+str(csv_file_name)+'.csv', 'r') as f:
            gotdata = csv.reader(f)
            for row in gotdata:
                URL_LIST.append(row[0])
                
        print("URL LIST:",URL_LIST)
        
        for URL in URL_LIST:
            
            print("\nURL:"+str(URL)+"\n")

            self.main_scrape(URL)
        
        gc.collect()
        return


    def img_scraper(self):
        
        urls = args.URL
        
        for url in urls:
            if url != "":
                print("\nURL:"+url)
                self.main_scrape(url)
            else:
                pass
            
        csv_file_names = args.csv
        for csv_file_name in csv_file_names:
            if csv_file_name != "":
                self.csv_reader(csv_file_name)
            else:
                pass    
        gc.collect()
        
        return
    
    
#----------------------------------------

if __name__ == '__main__':
    print("\n--------------------------------------------------------------------------------")
    time.sleep(0.02)
    print(r".__________                                        ")
    time.sleep(0.02)
    print(r" /   _____/ _______________  ______   ___________ ")
    time.sleep(0.015)
    print(r"  \_____  \_/ ___\_  __ \__  \ \____ \_/ __ \_  __ \ ")
    time.sleep(0.015)
    print(r" /        \  \___|  | \// __ \|  |_> >  ___/|  | \/")
    time.sleep(0.015)
    print(r"/_______  /\___  >__|  (____  /   __/ \___  >__|   ")
    time.sleep(0.01)
    print(r"/       \/     \/           \/|__|        \/       ")
    time.sleep(0.01)
    print("")
    time.sleep(0.005)
    print("--------------------------------------------------------------------------------\n")
    parser = argparse.ArgumentParser()
    parser.add_argument('URL', nargs='*', type=str, default=[''], help='url')
    parser.add_argument('--csv','-c', nargs='*', type=str, default=[], help='urls_csv')
    parser.add_argument('--node_number','-n', type=float, default=2.0, help='Enter the number to deley webscraping (optional)')
    parser.add_argument('--cooltime','-ct', type=float, default=0.0, help='COOL_TIME')
    parser.add_argument('--interval','-i', type=int, default=0, help='number of empty contents to randomize connection')
    parser.add_argument('--threads','-t', type=int, default=4, help='number of multithread core')
    parser.add_argument('--all',"-a", action='store_false',help="save all contents.")
    parser.add_argument('--silent_mode','-s', action='store_false',help="silent mode(unable to use multithread)")

    args = parser.parse_args()
    print(args)
    IS = AnonStaticWebScraper(args) 
    IS.img_scraper()

