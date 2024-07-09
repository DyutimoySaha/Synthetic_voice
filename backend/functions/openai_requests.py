import openai
from decouple import config

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from functions.database import get_recent_messages




# Retrieve Enviornment Variables
openai.organization = config("OPEN_AI_ORG")
openai.api_key = config("OPEN_AI_KEY")


# Open AI - Whisper
# Convert audio to text
def convert_audio_to_text(audio_file):
    try:
        response = openai.Audio.transcribe("whisper-1", audio_file,language="en")
        return response['text']
    except Exception as e:
        logger.exception("Error during audio transcription: %s", str(e))
        return None

# Open AI - Chat GPT
# Convert audio to text
def get_chat_response(message_input):

  messages = get_recent_messages()
  user_message = {"role": "user", "content": message_input}
  messages.append(user_message)
  # print(messages)

  try:
    response = openai.ChatCompletion.create(
      model="gpt-3.5-turbo",
      messages=messages
    )
    message_text = response["choices"][0]["message"]["content"]
    return message_text
  except Exception as e:
    return
