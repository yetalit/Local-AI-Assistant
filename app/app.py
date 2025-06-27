import os
import subprocess
from threading import Thread, Lock
import requests
import time
import json
import queue
import sys
from RealtimeSTT import AudioToTextRecorder
import re
from datetime import datetime
import note_manager
import pyttsx3


# --------------------------
# Configuration
# --------------------------
LLM_MODEL = "phi3.5:3.8b"
WHISPER_MODEL = 'small.en'
TTS_RATE = 170
TTS_VOICE_INDEX = 0
# --------------------------
# Shared resources
# --------------------------
engine_voices = pyttsx3.init().getProperty('voices')
stop_chars = ['.', ':', '!', '?']
sentence_queue = queue.Queue()
llm_buffer = ""

nm = note_manager.Manager()
note_lock = Lock()
taking_note = False
# --------------------------

def start_ollama():
    subprocess.Popen(
        ["ollama", "serve"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

def wait_then_pull(timeout=1):
    print("Waiting for Ollama server to start...")
    while True:
        try:
            response = requests.get("http://localhost:11434/api/tags")
            if response.status_code == 200:
                os.system("ollama pull " + LLM_MODEL)
                return
        except requests.exceptions.ConnectionError:
            print("!! Ollama not available yet. Retrying...")

        time.sleep(timeout)  # Wait before retrying

def tts_worker():
    while True:
        sentence = sentence_queue.get()
        if sentence is None:
            return  # Exit signal

        engine = pyttsx3.init()
        engine.setProperty('rate', TTS_RATE)
        engine.setProperty('voice', engine_voices[TTS_VOICE_INDEX].id)
        engine.say(sentence)
        engine.runAndWait()
        engine.stop()
        
        sentence_queue.task_done()

def substring_until_chars(s):
    indices = [s.find(c) for c in stop_chars if c in s]
    if indices:
        return (s[:min(indices)+1],s[min(indices)+1:])
    return (None, s)

def process_text(text):
    txt_lower = text.lower()
    command = command_cleaner(txt_lower)
    if command == 'takemenote' or command == 'takemenot':
        global taking_note
        taking_note = True
        sentence_queue.put('What is your note?')
    else:
        global llm_buffer
        if "explain" in txt_lower or "detailed" in txt_lower:
            prompt = text
        else:
            prompt = "Give a brief answer: " + text
        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={"model": LLM_MODEL, "prompt": prompt, "stream": True},
                stream=True,
            )
            print('----------------------------------------')
            for line in response.iter_lines():
                if not line:
                    continue
                try:
                    data = json.loads(line.decode("utf-8"))
                    chunk = data["response"]
                    audio, remaining = substring_until_chars(llm_buffer + chunk)
                    if audio:
                        sentence_queue.put(audio)
                    llm_buffer = remaining
                    print(chunk, end="", flush=True)
                except Exception as e:
                    sentence_queue.put(f"Error: {e}")

        except requests.RequestException as e:
            sentence_queue.put(f"Error: {e}")
        print('\n----------------------------------------')
    sentence_queue.join()

def command_cleaner(command):
    return re.sub(' |-|,', '', command.strip().rstrip(".").rstrip("!").rstrip("?"))
    
def set_date(date_str, clock_str):
    clock = command_cleaner(clock_str)
    try:
        date_part = datetime.strptime(command_cleaner(date_str), "%Y%B%d")

        hour = int(clock.split('.')[0])
        minute = int(int(clock.split('.')[1]))
        # Build full datetime
        full_dt = datetime(year=date_part.year, month=date_part.month, day=date_part.day, hour=hour, minute=minute, second=0)
        return full_dt
    except ValueError as e:
        print(f"Error parsing datetime: {e}")
        return None

def remind_note():
    while True:
        with note_lock:
            nm.move_past_notes()
        time.sleep(60)

if __name__ == '__main__':
    ollama = Thread(target=start_ollama, daemon=True)
    ollama.start()
    wait_then_pull()

    tts_thread = Thread(target=tts_worker, daemon=True)
    tts_thread.start()
    
    note_reminder = Thread(target=remind_note, daemon=True)
    note_reminder.start()
    
    print("Wait until it says 'speak now'")
    with AudioToTextRecorder(WHISPER_MODEL) as recorder:
        process_text('Hello')
        try:
            while True:
                process_text(recorder.text())
                
                if taking_note:
                    note = recorder.text() + '\n'
                    if command_cleaner(note.lower()) != 'cancel':
                        while True:
                            sentence_queue.put('Anything to add?')
                            sentence_queue.join()
                            additional_note = recorder.text() + '\n'
                            additional_note_lower = additional_note.lower()
                            if additional_note_lower.strip().rstrip(".").rstrip("!").rstrip("?") != 'no' and command_cleaner(additional_note_lower) != 'nope':
                                note += additional_note
                            else:
                                break

                        sentence_queue.put('Do you want to set a reminder?')
                        sentence_queue.join()
                        full_date = None
                        if command_cleaner(recorder.text().lower()) == 'yes':
                            sentence_queue.put('Tell me the year, month and the day?')
                            sentence_queue.join()
                            date = recorder.text()
                            sentence_queue.put('Tell me the hour point minute?')
                            sentence_queue.join()
                            clock = recorder.text()
                            full_date = set_date(date, clock)
                            if full_date is None:
                                sentence_queue.put('Error applying the date information!')
                                sentence_queue.join()
                                time.sleep(0.5)
                        
                        with note_lock:
                            nm.add_note(note, full_date)
                        sentence_queue.put('Note added!')
                        sentence_queue.join()
                    taking_note = False

        except KeyboardInterrupt:
            sentence_queue.put(None)
            tts_thread.join()
            print("\nProgram terminated.")
