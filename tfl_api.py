import sqlite3
import requests
import json
import os
import logging
import asyncio

from threads_api import publish_post
from logger_config import logger


MODES = ['tube', 'overground', 'dlr', 'elizabeth-line']

def get_tfl_line_status():
    modes = ','.join(MODES)
    url = f'https://api.tfl.gov.uk/Line/Mode/{modes}/Status'
    response = requests.get(url, headers={'Cache-Control': 'no-cache'})
    if response.status_code == 200:
        data = response.json()
        line_statuses = []
        for line in data:
            line_name = line['name']
            status = line['lineStatuses'][0]['statusSeverityDescription']
            status_details = line['lineStatuses'][0].get('reason', '')
            line_statuses.append((line_name, status, status_details))
        logger.info(f"Line statuses: {line_statuses}")
        return line_statuses
    else:
        logger.error(f"Failed to get TFL line status. Status code: {response.status_code}")
        return None
    
def get_sqlite_db():
    db_file = 'tfl_line_status.db'
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Create the table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS line_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            line_name TEXT,
            status TEXT,
            status_details TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Check if the threads_id column exists
    cursor.execute("PRAGMA table_info(line_status)")
    columns = [column[1] for column in cursor.fetchall()]
    
    # Add the threads_id column if it doesn't exist
    if 'threads_id' not in columns:
        cursor.execute('ALTER TABLE line_status ADD COLUMN threads_id TEXT')
        logger.info("Added threads_id column to line_status table")
    
    conn.commit()
    return conn

def save_line_status(line_statuses):
    conn = get_sqlite_db()
    cursor = conn.cursor()
    cursor.executemany('''
        INSERT INTO line_status (line_name, status, status_details)
        VALUES (?, ?, ?)
    ''', line_statuses)
    conn.commit()
    conn.close()

def get_recent_line_status(line_name):
    conn = get_sqlite_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM line_status WHERE line_name = ? ORDER BY timestamp DESC LIMIT 1', (line_name,))
    return cursor.fetchone()

def check_if_line_status_changed(line_name, new_status):
    recent_line_status = get_recent_line_status(line_name)
    if recent_line_status and recent_line_status[2] == new_status:
        return False
    return True

def get_lines_if_any_line_status_changed():
    line_statuses = get_tfl_line_status()
    lines_with_status_change = []
    for line_name, status, status_details in line_statuses:
        if check_if_line_status_changed(line_name, status):
            lines_with_status_change.append((line_name, status, status_details))
            save_line_status([(line_name, status, status_details)])
    return lines_with_status_change

def group_good_service_lines(lines_with_status_change):
    good_service_lines = []
    for line_name, status, status_details in lines_with_status_change:
        if status == 'Good Service':
            good_service_lines.append((line_name, status, status_details))
    return good_service_lines

def filter_out_good_service_lines(lines_with_status_change):
    return [line for line in lines_with_status_change if line[1] != 'Good Service']

async def main():
    lines_with_status_change = get_lines_if_any_line_status_changed()
    logger.info(f"Lines with status change: {lines_with_status_change}")
    good_service_lines = group_good_service_lines(lines_with_status_change)
    lines_with_status_change = filter_out_good_service_lines(lines_with_status_change)
    
    async def publish_bad_line_status(line_name, status, status_details):
        if status_details != '':
            msg = f"{status} on {line_name} \n\n {status_details}"
        
        logger.info(f"Publishing post: {msg}")
        await publish_post(msg)

    async def publish_good_service_combined_status(good_service_lines):
        msg = f"Good service reported again on {', '.join([line[0] for line in good_service_lines])}"
        logger.info(f"Publishing post: {msg}")
        await publish_post(msg)

    tasks = [
        publish_bad_line_status(line_name, status, status_details)
        for line_name, status, status_details in lines_with_status_change
    ]

    if len(good_service_lines) > 0:
        tasks.append(publish_good_service_combined_status(good_service_lines))
    
    await asyncio.gather(*tasks)

if __name__ == '__main__':
    asyncio.run(main())
