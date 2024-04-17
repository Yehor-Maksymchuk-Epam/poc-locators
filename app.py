from flask import Flask, request, jsonify
from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.options import Options
import openai

app = Flask(__name__)


@app.route('/uihelper', methods=['POST'])
def uihelper():
    data = request.json
    page_url = data['pageUrl']
    keywords = data['keyWords']
    print(page_url)
    for keyword in keywords:
        print(keyword)

    results = process_page(page_url, keywords)
    return jsonify(results)


def setup_selenium():
    options = Options()
    options.add_argument('--headless=new')
    driver = webdriver.Chrome(options=options)
    return driver


def process_page(page_url, keywords):
    driver = setup_selenium()
    driver.get(page_url)

    # Wait for page load if necessary
    driver.implicitly_wait(10)

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    driver.quit()

    return find_elements_in_ai(soup, keywords)
    # return find_elements(soup, keywords)


def find_elements(soup, keywords):
    results = {}
    for keyword in keywords:
        element = soup.find(id=keyword) or soup.find(class_=keyword)
        if element:
            results[keyword] = str(element)
        else:
            results[keyword] = 'Not Found'
    return results


def split_html(html, max_length=8000):
    chunks = []
    current_chunk = ''

    for line in html.split('\n'):
        if len(current_chunk) + len(line) + 1 > max_length:
            chunks.append(current_chunk)
            current_chunk = line
        else:
            current_chunk += line + '\n'

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def find_elements_in_ai(soup, keywords):
    client = openai.OpenAI()
    html = soup.prettify()
    chunks = split_html(html)
    for chunk in chunks:
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": f"""Please identify the locator for a specific UI element on a part of html code. I
                            will provide UI Element Name it is not a name or attribute name it is a keyword what can be used
                            to find element, like words cart, bucket etc for product cart on the online retail market
                            website. Here are the details: UI Elements : {keywords}
                                    Page code: {chunk}
                                I expect the output to provide the specific locator (either CSS
                                selector or XPath) of the mentioned UI element on the given webpage.
                                Please provide answer in JSON format only without suggestions or comments.
                                If locator not found send 404 Not Fount text in answer
                                """
                }
            ]
        )
        print(completion.choices[0].message.content)


if __name__ == '__main__':
    app.run(debug=True)
