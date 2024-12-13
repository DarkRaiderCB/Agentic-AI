from bs4 import BeautifulSoup as bs
from googlesearch import search
from rank_bm25 import BM25Okapi
import string
from sklearn.feature_extraction import _stop_words
from tqdm.autonotebook import tqdm
import numpy as np
import concurrent.futures
import time
import requests
import PyPDF2
import os
import re
import json
import warnings
from datetime import datetime
warnings.filterwarnings('ignore')


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
from openai import OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

def save_chat_history(chat_history, session_id):
    # Define the directory to store chat histories
    chat_dir = "chat_histories"
    os.makedirs(chat_dir, exist_ok=True)

    # Define the file path using the session ID
    file_path = os.path.join(chat_dir, f"chat_{session_id}.json")

    # Write the chat history to the file
    with open(file_path, "w") as file:
        json.dump(chat_history, file, indent=4)

def bm25_tokenizer(text):
    tokenized_doc = []
    for token in text.lower().split():
        token = token.strip(string.punctuation)

        if len(token) > 0 and token not in _stop_words.ENGLISH_STOP_WORDS:
            tokenized_doc.append(token)
    return tokenized_doc

def BM25func(passages, query):
    tokenized_corpus = []
    for passage in tqdm(passages):
        tokenized_corpus.append(bm25_tokenizer(passage))
    bm25 = BM25Okapi(tokenized_corpus)
    bm25_scores = bm25.get_scores(bm25_tokenizer(query))
    print("BM25 SCORES:", len(bm25_scores))
    try:
        top_n = np.argpartition(bm25_scores, -10)[-10:]
    except:
        try:
            top_n = np.argpartition(bm25_scores, -4)[-4:]
        except:
            top_n = np.argpartition(bm25_scores, -2)[-2:]

    bm25_hits = [{'corpus_id': idx, 'score': bm25_scores[idx]} for idx in top_n]
    bm25_hits = sorted(bm25_hits, key=lambda x: x['score'], reverse=True)
    bm25_passages = []
    for hit in bm25_hits:
        bm25_passages.append(' '.join(passages[hit["corpus_id"].split()[:100]]))
    print(bm25_passages)
    return bm25_passages

def scraper(url, con, DataWrtUrls, passages):
    # print("Scraper running")
    session = requests.Session()
    my_headers = {"User-Agent": "Mozilla/5.0 (X11; CrOS x86_64 14685.0.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.4992.0 Safari/537.36",
                  "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"}
    result = session.get(url, headers=my_headers, verify=False, timeout=3)
    doc = bs(result.content, "html.parser")
    contents = doc.find_all("p")
    for content in contents:
        passages.append(content.text)
        con.append(content.text + "\n")

    DataWrtUrls[url] = str(con)

def extract_links(URLs):
    session = requests.Session()
    my_headers = {"User-Agent": "Mozilla/5.0 (X11; CrOS x86_64 14685.0.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.4992.0 Safari/537.36",
                  "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"}
    extracted_content = []
    for url in URLs:
        try:
            if url.endswith('.pdf'):
                extracted_content.append(scrape_pdf(url))
                continue
            result = session.get(url, headers=my_headers, verify=False, timeout=3)
            doc = bs(result.content, "html.parser")
            contents = doc.find_all("p")
            for content in contents:
                extracted_content.append(content.text)
        except:
            pass
    return extracted_content  # list of strings

def scrape_pdf(url):
    session = requests.Session()
    my_headers = {
        "User-Agent": "Mozilla/5.0 (X11; CrOS x86_64 14685.0.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.4992.0 Safari/537.36",
        "Accept": "application/pdf"
    }
    result = session.get(url, headers=my_headers, verify=False, timeout=3)
    with open("./temp.pdf", "wb") as f:
        f.write(result.content)
    extracted_texts = []
    with open("./temp.pdf", "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            extracted_texts.append(page.extract_text())
    extracted_text = " ".join(extracted_texts)
    return extracted_text

def extract_unique_urls(input_string):
    regex_patterns = [
        r'(https?://\S+)',  # Matches HTTP and HTTPS URLs
        r'(www\.\S+\.\w+)',  # Matches URLs starting with www
        r'(ftp://\S+)',  # Matches FTP URLs
    ]

    extracted_urls = []

    for pattern in regex_patterns:
        matches = re.findall(pattern, input_string)
        extracted_urls.extend(matches)

    unique_urls = set(extracted_urls)

    return unique_urls

def web_search(query, relevanceSort=False):
    session_id = datetime.now().strftime("%Y%m%d%H%M%S")
    chat_history = []
    system_prompt = """You are a software requirement gathering assistant. Your role is to interpret any user input, even if seemingly unrelated, as potential requirements or ideas for a software system. Respond in a way that identifies goals, features, and constraints of the system the user might need.
                   Always:
                    1. Map user input to relevant software requirements or use cases, explaining your interpretation.
                    2. Focus on understanding the user's objectives and intended workflows.
                    3. Handle irrelevant queries by asking follow up questions and attempting to identify underlying needs or problems that could inspire a software solution.
                    4. If present, format code snippets within ''' ''' triple quotes.
                    5. IMPORTANT: Ask follow up questions with heading "FOLLOW-UP QUESTIONS" to seek clarity and better understand user needs, but eventually stop once sufficient details are collected.
                    6. If the user input suggests that further changes are not required, then stop asking follow up questions.
                    7. Once no further changes are required by user, mention all the requirements, keeping in mind the complete conversation, in a structured manner in the final response.
                   
                    For example:
                    1. If the user says, \"I hate waiting for taxis,\" infer a need for a system that reduces waiting times, such as a ride-booking app with real-time tracking.
                    2. If the user asks about organizing a birthday party, consider software to manage events or reminders.
                   
                   Always ensure your responses are structured and actionable for software designers."""
    chat_history.append({"role": "system", "content": system_prompt})
    customer_message = query
    unique_urls = extract_unique_urls(customer_message)
    extracted_content = []
    if unique_urls:
        extracted_content = extract_links(list(unique_urls))
        print("Extracting content from URLs")
    bi_encoder_searched_passages = ""
    urls = []
    passages = []
    con = []
    start = time.time()
    search_results = list(search(customer_message, tld="com", num=10, stop=10, pause=0.75))  # URL searching
    for j in search_results:
        urls.append(j)
    print("URLS=", urls)
    DataWrtUrls = {}
    passages = []
    time_for_scraping = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(scraper, url, con, DataWrtUrls, passages): url for url in urls}

        for future in concurrent.futures.as_completed(futures):
            url = futures[future]
            try:
                result = future.result()
            except Exception as exc:
                print(f'URL {url} generated an exception: {exc}')
    print("time for scraping: ", time.time() - time_for_scraping)
    passages2 = []
    i = 0
    try:
        while i < len(passages):
            P = ""
            while len(P.split()) <= 80 and i < len(passages):
                P += (passages[i] + " ")
                i += 1
            passages2.append(P.strip())
    except Exception as exc:
        print(f"Error processing passages: {exc}")
    end = time.time() - start

    start = time.time()

    if len(extracted_content) > 0:
        i = min(len(passages2), len(extracted_content))
        for j in range(i):
            passages2[j] = extracted_content[j]
            extracted_content.pop(j)
        for j in range(len(extracted_content)):
            passages2.append(extracted_content[j])

    if relevanceSort:
        bi_encoder_searched_passages = BM25func(passages2, customer_message)
    else:
        bi_encoder_searched_passages = passages2
    question = customer_message

    if len(bi_encoder_searched_passages) >= 7:
        supporting_texts = "Supporting Text 1: " + str(bi_encoder_searched_passages[0]) + "\nSupporting Text 2: " + str(bi_encoder_searched_passages[1]) + "\nSupporting Text 3: " + str(bi_encoder_searched_passages[2]) + "\nSupporting Text 4: " + str(bi_encoder_searched_passages[3]) + "\nSupporting Text 5: " + str(bi_encoder_searched_passages[4]) + "\nSupporting Text 6: " + str(bi_encoder_searched_passages[5]) + "\nSupporting Text 7: " + str(bi_encoder_searched_passages[6])
    else:
        supporting_texts = ""
        for i in range(len(bi_encoder_searched_passages)):
            supporting_texts += "Supporting Text " + str(i + 1) + ": " + str(bi_encoder_searched_passages[i]) + "\n"
    
    user_prompt = f"""Question: {str(question)}\n
                    Supporting Information:
                    {str(supporting_texts)}\n
                    Based on the above, identify actionable software requirements. If the input is unclear, hypothesize potential software needs."""
    
    chat_history.append({"role": "user", "content": user_prompt})
    
    while True:
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=chat_history
        )

        output = completion.choices[0].message.content
        print(f"GPT: {output}")
        chat_history.append({"role": "assistant", "content": output})
        save_chat_history(chat_history, session_id)
        sanitized = re.sub(r'[^a-zA-Z0-9\s]', ' ', output)
        sanitized = sanitized.lower()
        if "follow up questions" not in sanitized:
            print("Exiting!")
            break
        follow_up = input("You: ")
        chat_history.append({"role": "user", "content": follow_up})
    return f"chat_histories/chat_{session_id}.json"

# if __name__ == "__main__":
#     print("Initializing response flow.")

#     query = input("Enter your query: ")
#     web_search(query)