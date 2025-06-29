# Local AI Assistant

An AI voice assistant working fully locally. It's also able to perform tasks.

### Supported Tasks

Following tasks are implemented:

* Taking notes and setting reminders for them.

## Getting Started

### Dependencies

* Ollama
* PyTorch
* RealtimeSTT
* pyttsx3

### Installing

#### Ollama

First, you need to install Ollama: https://ollama.com/download

#### Pip Packages

Then, Install necessary pip packages using:

```
pip install RealtimeSTT pyttsx3
```

To install the gpu version of PyTorch:

```
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### Executing program

Download the app folder and Run `app.py` script in background:

```
python app.py &
```

You can configure the models and parameters at the beginning of the script:

```
# --------------------------
# Configuration
# --------------------------
LLM_MODEL = "phi3.5:3.8b"
WHISPER_MODEL = 'small.en'
TTS_RATE = 170
TTS_VOICE_INDEX = 0
```

## Commands for Tasks

### Notes and Reminders

Command for taking notes is:

```
Take me note
```

* Use `yes` and `no` to give positive and negative responses.
* The format to give the day, month and the year information: `<day> <month name> <year>` for example, 2025-06-29 -> `29 June 2025`
* The format to give the clock information: `<hour>.<minute>` for example, 1:05 PM -> `13.5`
