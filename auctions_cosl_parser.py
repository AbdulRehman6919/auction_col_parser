from playwright.sync_api import sync_playwright
import time 
import pandas as pd
from tqdm import tqdm
import traceback

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto('https://auction.cosl.org/Auctions/ListingsView')


    all_data=[] #all data comes here

    while True:

        # Locate the table
        table = page.locator('//*[@id="grid"]/div[3]/table')
        # Extract table headers
        headers = table.locator('thead tr th').all_text_contents()
        # Extract table rows
        rows = table.locator('tbody tr')
        data = []  
        for row in rows.element_handles():
            cells = row.query_selector_all('td')
            data.append([cell.inner_text() for cell in cells])

        for index, temp_row in tqdm(enumerate(data), total=len(data)):

            try:
                if "Bid"  in temp_row[-1] and "Map"  in temp_row[-1]:
                    # print(row) #both options valid
                    xpath = '//*[@id="grid"]/div[3]/table/tbody/tr['+str(index+1)+']/td[11]/div/a[2]'
                    print(xpath)
                elif "Bid" in temp_row[-1]:
                    xpath = '//*[@id="grid"]/div[3]/table/tbody/tr['+str(index+1)+']/td[11]/div/a'
                    print(xpath)

                # Locate the xpath element
                bid_button = page.wait_for_selector(xpath)
                
                #Scraping all the required details
                auction_link = "https://auction.cosl.org"+bid_button.get_attribute("href")
                parcel_num = temp_row[2]
                starting_bid = temp_row[-4]
                current_bid = temp_row[-3]
            
                all_data.append([auction_link, parcel_num, starting_bid, current_bid ])

                pd.DataFrame(all_data, columns = ["Action Link", "Parcel Num#", "Starting Bid", "Current Bid"]).to_csv("auctions_col_parser.csv", index=False)

            except:
                print(traceback.print_exc())
                break 

        # Check if the "Next Page" button is present and enabled
        next_button = page.locator('css=#grid > div.k-pager-wrap.k-grid-pager.k-widget.k-floatwrap > a:nth-child(4) > span')

        try:  
            next_button.click()  # Go to the next page
            time.sleep(5)  # Wait for data to load
        except:
            print("No more pages left.")
            break  # Exit loop if there are no more pages

    context.close()
    browser.close()
