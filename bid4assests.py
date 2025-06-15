from playwright.sync_api import sync_playwright
import time 
import pandas as pd
import traceback
from bs4 import BeautifulSoup
import requests
from tqdm import tqdm

def get_specific_data(url_link, storefrontId, storefrontCollectionId):

    url = "https://www.bid4assets.com/api/storefront/auctions/index"
    params = {
        "take": 9999,
        "skip": 0,
        "page": 1,
        "pageSize": 9999
    }

    payload = {
        "storefrontId": storefrontId,
        "storefrontCollectionId": storefrontCollectionId
    }

    headers = {
        "Host": "www.bid4assets.com",
        "Origin": "https://www.bid4assets.com",
        "Referer": url_link,
        "Request-Context": "appId=cid-v1:b4ca208b-af26-4b31-bd42-311b8cb0180f",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
        "Sec-Ch-Ua": '"Chromium";v="134", "Not A-Brand";v="24", "Google Chrome";v="134"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, params=params, headers=headers)

    # Print response status and content
    print(response.status_code)
    return response.json()  



with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto('https://www.bid4assets.com/county-tax-sales',timeout= 60000)


    content = page.content()  # Get the full page source (HTML)
    with open("page_content.txt", "w", encoding="utf-8") as file:
        file.write(content)  # Save content to a text file
    print("Page content saved to page_content.txt")

    #Scraping the calender clickable link
    html_content = page.content() 
    all_auction_list = []
    soup = BeautifulSoup(html_content, "html.parser")
    for temp_data in soup.find('div', class_='carousel-inner').find_all(class_='month active'):
        all_auction_list+=temp_data.find('ul',class_='auction-list').find_all('li')

    print("All auctions List: ", all_auction_list)

    all_auctions = []
    for index, single_action in enumerate(all_auction_list):
        try:

            link = "https://www.bid4assets.com"+single_action.a['href']
            print("Scraping Link: ", link)

            #Going inside the each county 

            page2 = browser.new_context().new_page()
            if index ==0:
                page.close()


            page2.goto(link, timeout= 120000)


            element = page2.locator("#auction-folders-wp").click()

            html_inner_content = page2.content() 
            soup = BeautifulSoup(html_inner_content, "html.parser")


            list_of_records = [i['id'].strip('ac-') for i in soup.find_all('input', attrs={'name':"accordion-1"} ) if len(i['id'])>6]
            print("List of records: ", list_of_records)

            StoreFrontId = soup.find('input', attrs={'name':"StorefrontId"})['value']
            print("StoreFrontId: ", StoreFrontId)

            if StoreFrontId and len(list_of_records) >=1:
                for auction_id in tqdm(list_of_records):
                    try:
                        data = get_specific_data(link, StoreFrontId, auction_id) 
                        if len(data['data'])>0:
                            for row in data['data']:
                                auction_url = "https://www.bid4assets.com/auction/index/"+str(row['auctionID'])

                                if row['timeRemaining'].strip() !='Closed' or row['timeRemaining'] !='Sold':
                                    all_auctions.append([row['auctionID'],auction_url,  row['minimumBid'],row['currentBidAmount'],row['timeRemaining'], link])

                            pd.DataFrame(all_auctions, columns = ['AuctionID','AuctionURL','MinimumBid','CurrentBidAmount','TimeRemaining','LinkOrignated']).to_csv("bid4assests_auctions.csv",index=None)

                    except:
                        print(traceback.print_exc())


            time.sleep(3)
            page2.close()
            print("Link Scpared: ", link)
        except:
            print(traceback.print_exc())
            pass
            

    time.sleep(3)

    browser.close()
