import os
import shutil
import pandas as pd
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
import re

WATCH_DIR = 'watch_folder/incoming'
DEST_DIR = 'watch_folder/processed'
MASTER_CSV = 'watch_folder/master.csv'

VALID_PARTNERS = {'PAZ', 'F7R', 'KOMPSAT-5'}

def parse_txt_file(file_path):
    entries = []
    session_id = None

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()

            # look for session ID
            session_match = re.match(r'^J\d{3}$', line)
            if session_match:
                session_id = session_match.group(0)
                continue

            # match support line: partner, ID, date, start, finish, antenna
            parts = line.split()
            if len(parts) >= 6 and parts[0] in VALID_PARTNERS:
                partner = parts[0]
                date = parts[2]
                start_time = parts[3]
                finish_time = parts[4]
                antenna = parts[5]

                entries.append({
                    'Session': session_id,
                    'Partner': partner,
                    'Date': date,
                    'Start Time': start_time,
                    'Finish Time': finish_time,
                    'Antenna': antenna
                })
        

def process_file(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.txt':
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        df = pd.DataFrame([line.strip() for line in lines if line.strip()], columns=['Data'])
        
    elif ext == '.xlsx':
        df = pd.read_excel(file_path)
    else:
        print(f"Unsupported file type: {ext}")
        return
    
    if os.path.exists(MASTER_CSV):
        d.to_csv(MASTER_CSV, mode='a', header=False, index=False)
    else:
        df.to_csv(MASTER_CSV, index=False)
    
    # Move the processed file to the destination directory
    shutil.move(file_path, os.path.join(DEST_DIR, os.path.basename(file_path)))
    print(f"Processed and moved file: {file_path}")

class WatcherHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith(('.txt', '.xlsx')):
            print(f"New file detected: {event.src_path}")
            time.sleep(1) # Allow time for the file to be fully written
            process_file(event.src_path)

if __name__ == "__main__":
    if not os.path.exists(WATCH_DIR):
        os.makedirs(WATCH_DIR)
    if not os.path.exists(DEST_DIR):
        os.makedirs(DEST_DIR)

    print(f"Watching directory: {WATCH_DIR}")
    observer = Observer()
    event_handler = WatcherHandler()
    observer.schedule(event_handler, path=WATCH_DIR, recursive=False)
    
    print("Starting file watcher...")
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    
    observer.join()