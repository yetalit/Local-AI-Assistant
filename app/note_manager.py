import json
import os
from datetime import datetime
from pathlib import Path
from plyer import notification


BASE_FOLDER = os.path.join(os.getcwd(), 'Phi Notes')
NOTES_FILE = os.path.join(BASE_FOLDER, 'notes.json')
PAST_FOLDER = os.path.join(BASE_FOLDER, 'reminded')
PAST_NOTES_FILE = os.path.join(PAST_FOLDER, 'notes.json')

# Ensure the base folders exist
Path(BASE_FOLDER).mkdir(parents=True, exist_ok=True)
Path(PAST_FOLDER).mkdir(parents=True, exist_ok=True)

def load_notes(file_path):
    if not os.path.exists(file_path):
        return {'dated_notes': {}, 'undated_notes': []}
    with open(file_path, 'r') as f:
        return json.load(f)

def save_notes(notes, file_path):
    with open(file_path, 'w') as f:
        json.dump(notes, f, indent=4)

def add_note(note_text, datetime_obj=None):
    notes = load_notes(NOTES_FILE)
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if datetime_obj:
        datetime_key = datetime_obj.strftime('%Y-%m-%d %H:%M')
        if datetime_key not in notes['dated_notes']:
            notes['dated_notes'][datetime_key] = []
        notes['dated_notes'][datetime_key].append({'note': note_text, 'added_on': current_time})
    else:
        notes['undated_notes'].append({'note': note_text, 'added_on': current_time})

    save_notes(notes, NOTES_FILE)

def move_past_notes():
    notes = load_notes(NOTES_FILE)
    past_notes = load_notes(PAST_NOTES_FILE)
    now = datetime.now()

    to_move = {}

    for datetime_str in list(notes['dated_notes']):
        note_time = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M')
        if note_time <= now:
            note_list = notes['dated_notes'].pop(datetime_str)
            to_move[datetime_str] = note_list
            for note in note_list:
                notification.notify(
                title='Phi Note Reminder',
                message=note['note'],
                timeout=5
                )
                
    if to_move:
        if 'dated_notes' not in past_notes:
            past_notes['dated_notes'] = {}
        past_notes['dated_notes'].update(to_move)

        save_notes(notes, NOTES_FILE)
        save_notes(past_notes, PAST_NOTES_FILE)
        
class Manager:
    def __init__(self):
        self.notes = self._load_notes(NOTES_FILE)
        self.past_notes = self._load_notes(PAST_NOTES_FILE)

    def _load_notes(self, file_path):
        if not os.path.exists(file_path):
            return {'dated_notes': {}, 'undated_notes': []}
        with open(file_path, 'r') as f:
            return json.load(f)
    
    def _save_notes(self, notes, file_path):
        with open(file_path, 'w') as f:
            json.dump(notes, f, indent=4)

    def add_note(self, note_text, datetime_obj=None):
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if datetime_obj:
            datetime_key = datetime_obj.strftime('%Y-%m-%d %H:%M')
            if datetime_key not in self.notes['dated_notes']:
                self.notes['dated_notes'][datetime_key] = []
            self.notes['dated_notes'][datetime_key].append({'note': note_text, 'added_on': current_time})
        else:
            self.notes['undated_notes'].append({'note': note_text, 'added_on': current_time})

        self._save_notes(self.notes, NOTES_FILE)
    
    def move_past_notes(self):
        now = datetime.now()
        to_move = {}

        for datetime_str in list(self.notes['dated_notes']):
            note_time = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M')
            if note_time <= now:
                note_list = self.notes['dated_notes'].pop(datetime_str)
                to_move[datetime_str] = note_list
                for note in note_list:
                    notification.notify(
                    title='Phi Note Reminder',
                    message=note['note'],
                    timeout=5
                    )
        
        if to_move:
            if 'dated_notes' not in self.past_notes:
                self.past_notes['dated_notes'] = {}
            self.past_notes['dated_notes'].update(to_move)

            self._save_notes(self.notes, NOTES_FILE)
            self._save_notes(self.past_notes, PAST_NOTES_FILE)
