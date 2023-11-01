import boto3
import requests
from bs4 import BeautifulSoup

OPENAI_API_URL = "https://api.openai.com/v1/completions"  
OPENAI_API_KEY = "your own OpenAI code"  # Replace with your OpenAI API key

def get_opposite_text(text):
    # Construct the prompt for OpenAI
    prompt = f"Rewrite this statement to convey the opposite meaning: '{text}'?"

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "prompt": prompt,
        "max_tokens": 150,  # Limit the output length
        "model":"text-davinci-003"
    }

    response = requests.post(OPENAI_API_URL, headers=headers, json=data)
    response.raise_for_status()

    opposite_text = response.json().get("choices")[0].get("text").strip()
    return opposite_text

def insert_disclaimer(soup):
    # Find the h1 tag with the given id
    h1_tag = soup.find('h1', id="page-title")
    
    if h1_tag:
        # Create the new disclaimer div
        disclaimer_div = soup.new_tag("div")
        disclaimer_div['class'] = "disclaimer"
        disclaimer_div['style'] = "background-color: #f2f2f2; padding: 10px; text-align: center;"

        p_tag = soup.new_tag("p")
        p_tag.string = "Disclaimer: The contents in this site are altered from original sources (BBC) using AI. This site is purely for educational purposes."

        disclaimer_div.append(p_tag)
        
        # Insert the disclaimer div after the h1 tag
        h1_tag.insert_after(disclaimer_div)
    
    return soup


def lambda_handler(event, context):
    # Fetch the saved content from S3
    s3_bucket_name = 'fakebbc.com'
    s3_source_bucket_name = 'ailifestylecbb'
    s3_file_name = 'bbc_front_page.html'
    s3_client = boto3.client('s3')
    s3_file_new_name='index.html'

    response = s3_client.get_object(Bucket=s3_source_bucket_name, Key=s3_file_name)
    raw_html = response["Body"].read().decode()

    # Parse the content with BeautifulSoup
    soup = BeautifulSoup(raw_html, 'html.parser')
    
    # Insert the disclaimer
    soup = insert_disclaimer(soup)
    

    # Find headlines
    media_contents = soup.find_all('div', class_='media__content')

    for media_content in media_contents:
        headline_tag = media_content.find('a', class_='media__link')
        if headline_tag:
            original_headline = headline_tag.get_text(strip=True)
            opposite_headline = get_opposite_text(original_headline)
            headline_tag.string.replace_with(opposite_headline)

        summary_tag = media_content.find('p', class_='media__summary')
        if summary_tag:
            original_summary = summary_tag.get_text(strip=True)
            opposite_summary = get_opposite_text(original_summary)
            summary_tag.string.replace_with(opposite_summary)

    # Serialize the modified content
    modified_content = str(soup)
    
    # Optionally, save the modified content back to S3 or elsewhere
    s3_client.put_object(Bucket=s3_bucket_name, Key=s3_file_new_name, Body=modified_content,ContentType='text/html',ACL='public-read')
    
    return {
        'statusCode': 200,
        'body': 'Content modified successfully!'
    }
