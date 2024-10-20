import os
from time import sleep
import requests
import asyncio
from logger_config import logger

THREADS_API_TOKEN = os.environ.get('THREADS_API_TOKEN')

THREADS_API_URL = 'https://graph.threads.net/'

THREADS_API_VERSION = 'v1.0'

THREADS_USER_ID = os.environ.get('THREADS_USER_ID')

def create_threads_post(text_content):
    """
    Create a text post and publish it to Threads.
    
    :param text_content: The content of the post
    :return: The response from the API
    """
    # Truncate text_content if it's longer than 500 characters
    if len(text_content) > 500:
        text_content = text_content[:496] + "..."

    endpoint = f"{THREADS_API_URL}{THREADS_API_VERSION}/{THREADS_USER_ID}/threads"
    
    headers = {
        'Authorization': f'Bearer {THREADS_API_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'media_type': 'TEXT',
        'text': text_content
    }
    
    response = requests.post(endpoint, headers=headers, json=payload)
    if response.status_code != 200:
        logger.error(f"Failed to create post: {response.status_code} {response.text}")
        # Retry after 5 seconds
        sleep(5)
        response = create_threads_post(text_content)
    return response.json()


def publish_post_from_creation_id(post_id):
    endpoint = f"{THREADS_API_URL}{THREADS_API_VERSION}/{THREADS_USER_ID}/threads_publish"
    headers = {
        'Authorization': f'Bearer {THREADS_API_TOKEN}',
        'Content-Type': 'application/json'
    }
    payload = {
        'creation_id': post_id 
    }

    response = requests.post(endpoint, headers=headers, json=payload)
    return response.json()

async def publish_post(text_content):
    
    creation_id = create_threads_post(text_content)['id']
    await asyncio.sleep(5)
    return publish_post_from_creation_id(creation_id)

