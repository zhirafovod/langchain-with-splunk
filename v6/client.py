import requests
import time
import random

# List of sample questions to demonstrate different tools
questions = [
    "Tell me about Apple Inc.",           # Uses company_info tool
    "What is the capital of France?",     # Uses general_knowledge tool
    "What is the latest news about Tesla?" # Uses web_search_tool
]

print("Starting client to make periodic requests to the server...")
while True:
    question = random.choice(questions)
    try:
        response = requests.post(
            "http://localhost:8080/askquestion",
            json={"question": question}
        )
        if response.status_code == 200:
            print(f"Question: {question}")
            print(f"Response: {response.text}\n")
        else:
            print(f"Error: Received status code {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    time.sleep(10)  # Wait 10 seconds before the next request