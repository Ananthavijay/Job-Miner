# imports
import requests
from bs4 import BeautifulSoup
from datetime import date
import pandas as pd
import boto3
from botocore.client import Config
import openpyxl

# amazon s3 configurations
ACCESS_KEY_ID = ''
ACCESS_SECRET_KEY = ''
BUCKET_NAME = 'jobs-csv-storage'

filename = 'job_list.xlsx'

# function to generate url
def generate_url(keyword,location):
    url = 'https://in.indeed.com/jobs?q={}&l={}'.format(keyword,location)
    return url

# function to generate html content (soup object)
def extract_data(url):
    headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.72 Safari/537.36'}
    r = requests.get(url, headers)
    soup = BeautifulSoup(r.content, 'html.parser')
    return soup

# function to scrape data
def transform_data(soup, joblists):
    divs = soup.find_all('div', class_="jobsearch-SerpJobCard")
    for item in divs:
      title = item.find('a').text.strip()
      company = item.find('span', class_='company').text.strip()
      location = item.find(class_='location').text.strip()
      try:
        salary = item.find('span', class_='salaryText').text.strip()
      except AttributeError:
        salary = ''
      summary = item.find('div', class_='summary').text.strip().replace('\n','')
      posted_date = item.find('span', class_='date').text
      today_date = date.today().strftime("%d/%m/%Y")
      base_url = "https://indeed.com"
      link = item.find('a').attrs['href']

      job = {
          'Title': title,
          'Company': company,
          'Location': location,
        # 'Rating': rating,
          'Salary': salary,
          'Summary': summary,
          "Today's date": today_date,
          'Posted': posted_date,
          'Link': base_url + link
      }
      joblists.append(job)
    return joblists

# function to get url of the next page
def get_next_page(soup):
    try:
        url = soup.find("a", {"aria-label": "Next"}).get("href")
        return "https://in.indeed.com" + url
    except AttributeError:
        return None

# function to save dataframe to xlsx
def save_to_xlsx(df):
    df.to_excel(filename, encoding='utf-8', columns=["Title","Company","Location","Salary","Today's date","Posted","Link"])

# function to upload xlsx to amazon s3 -> For heroku deployment
def to_aws():
    data = open(filename, 'rb')
    # connect to AWS
    s3 = boto3.resource(
        's3',
        aws_access_key_id=ACCESS_KEY_ID,
        aws_secret_access_key=ACCESS_SECRET_KEY,
        config=Config(signature_version='s3v4')
    )
    # file upload
    s3.Bucket(BUCKET_NAME).put_object(Key=filename, Body=data, ACL='public-read')

# main function
def extract_job(keyword=None,location=None):

    joblists = []

    if not location and not keyword:
        return 0
    url = generate_url(keyword,location)
    for _ in range(4):
        c = extract_data(url)
        if not url:
            break
        joblists = transform_data(c,joblists)
        url = get_next_page(c)
        if not url:
            break

    df = pd.DataFrame(joblists)
    if len(df)>0:
        save_to_xlsx(df)
        to_aws()
    return len(df) # returns the number of jobs
