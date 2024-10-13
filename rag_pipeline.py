import os
import torch
import re
import json
import numpy as np
import requests
import time
from sentence_transformers import SentenceTransformer
import faiss


# Set the Hugging Face API token (make sure it's stored securely)
os.environ["HUGGINGFACE_TOKEN"] = "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"

API_URL = "https://api-inference.huggingface.co/models/meta-llama/Meta-Llama-3-8B-Instruct"
headers = {"Authorization": f"Bearer {os.environ['HUGGINGFACE_TOKEN']}"}


# Load and clean the scraped data
def load_scraped_data(scraped_data_file):
    with open(scraped_data_file, 'r') as file:
        scraped_data = json.load(file)

    def clean_markdown(text):
        if not isinstance(text, str):
            return ""
        text = re.sub(r'!\[.*?\]\(.*?\)', '', text)  # Remove images
        text = re.sub(r'\[.*?\]\(.*?\)', '', text)  # Remove links
        text = ' '.join(text.split())  # Normalize whitespace
        return text

    for entry in scraped_data:
        markdown_content = entry.get("markdown", "")
        entry["cleaned_markdown"] = clean_markdown(markdown_content)

    return scraped_data


# Function to extract contact information from query
def extract_contact_form_info(query):
    form_data = {
        "event": re.search(r'Veranstaltung:\s*([^\s]+)', query),
        "first_name": re.search(r'Vorname:\s*([^\s]+)', query),
        "last_name": re.search(r'Nachname:\s*([^\s]+)', query),
        "birth_date": re.search(r'Geburtsdatum:\s*([^\s]+)', query),
        "address": re.search(r'Adresse:\s*(.+?)\s*E-Mail:', query),
        "email": re.search(r'E-Mail:\s*([^\s]+)', query),
        "phone": re.search(r'Telefon:\s*([^\s]+)', query),
        "message": re.search(r'Mitteilung:\s*(.*)', query, re.DOTALL)
    }
    extracted_info = {key: match.group(1).strip() if match else None for key, match in form_data.items()}
    return extracted_info


# Function to handle API request with retry logic
def send_to_huggingface_api(payload):
    response = requests.post(API_URL, headers=headers, json=payload)
    return response.json()


def send_with_retry(payload, max_retries=10, wait_time=30):
    retries = 0
    while retries < max_retries:
        response = send_to_huggingface_api(payload)
        if 'error' in response and 'loading' in response['error']:
            print(f"Model is loading, retrying in {wait_time} seconds... ({response['estimated_time']} seconds estimated)")
            time.sleep(wait_time)
            retries += 1
        else:
            return response
    return {"error": "Model failed to load after multiple retries."}


# The main RAG pipeline function
def rag_pipeline(query, sentence_model, index, scraped_data):
    # Parse the query and extract contact form information
    contact_info = extract_contact_form_info(query)
  
    # Encode the cleaned query and retrieve relevant documents
    cleaned_query = query 
    query_embedding = sentence_model.encode(cleaned_query)
    
    # Retrieve top-k relevant documents using FAISS
    k = 3
    distances, indices = index.search(np.array([query_embedding]), k)
    retrieved_docs = [scraped_data[i] for i in indices[0]]
    
    # Combine retrieved documents into a single context
    context = " ".join([doc['cleaned_markdown'][:1500] for doc in retrieved_docs])
    context = context + "27.10.2024"

    # Create a prompt for the email response
    prompt = f"""
    The user has the following query: "{cleaned_query}"
    Only if he asks, otherwise ignore:
    Use the context provided below to craft a professional response as an email.

    Context:
    {context}
    

    Email format:
    - Start with a greeting (e.g., "Dear [name],")
    - Include a clear response addressing the user's query.
    - End with a professional sign-off (e.g., "Best regards, \nYour DataSport Team" or "Sincerely, \nYour DataSport Team")
    - No more text after this.

    Answer:
    """

    # Send the prompt to Hugging Face API with stop_sequence
    payload = {
       "inputs": prompt,
       "parameters": {
           "max_new_tokens": 100,
           "stop": ["Best regards, \nYour DataSport Team"],
           "temperature": 0.9,
       }
    }
    api_response = send_with_retry(payload)
    
    # Extract and return the generated response
    if 'error' in api_response:
        return f"Error: {api_response['error']}"
    
    generated_response = api_response[0]['generated_text'][len(prompt):]
    return generated_response


# Load sentence transformer model and scraped data
def setup_pipeline(scraped_data_file):
    sentence_model = SentenceTransformer('all-mpnet-base-v2')
    scraped_data = load_scraped_data(scraped_data_file)

    # Generate embeddings and create FAISS index
    embeddings = np.array([sentence_model.encode(entry['cleaned_markdown']) for entry in scraped_data])
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)
    return sentence_model, index, scraped_data


# Main execution function to take user query and return generated answer
def get_email(query):
    # Setup models and data
    sentence_model, index, scraped_data = setup_pipeline('scraped_data.json')
    
    # Get the generated answer
    generated_answer = rag_pipeline(query, sentence_model, index, scraped_data)
    return generated_answer
   


if __name__ == "__main__":
    get_email()
