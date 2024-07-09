# uvicorn main:app
# uvicorn main:app --reload

# Main imports
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from decouple import config
import openai
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



# Custom function imports
from functions.text_to_speech import convert_text_to_speech
from functions.openai_requests import convert_audio_to_text, get_chat_response
from functions.database import store_messages, reset_messages


# Get Environment Vars
openai.organization = config("OPEN_AI_ORG")
openai.api_key = config("OPEN_AI_KEY")


# Initiate App
app = FastAPI()


# CORS - Origins
origins = [
    "http://localhost:5175",
    "http://localhost:5174",
    "http://localhost:5173",
    "http://localhost:3000",
]


# CORS - Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Check health
@app.get("/health")
async def check_health():
    return {"response": "healthy"}


# Reset Conversation
@app.get("/reset")
async def reset_conversation():
    reset_messages()
    return {"response": "conversation reset"}


# Post bot response
# Note: Not playing back in browser when using post request.
@app.post("/post-audio/")
async def post_audio(file: UploadFile = File(...)):
    try:
        logger.info("Received file: %s", file.filename)

        # Save the file temporarily
        temp_file_path = file.filename
        with open(temp_file_path, "wb") as buffer:
            buffer.write(file.file.read())
        logger.info("File saved: %s", temp_file_path)

        # Open the saved file for reading
        with open(temp_file_path, "rb") as audio_input:
            # Convert audio to text
            message_decoded = convert_audio_to_text(audio_input)
            logger.info("Decoded message: %s", message_decoded)

        # Clean up the temporary file
        os.remove(temp_file_path)
        logger.info("Temporary file deleted: %s", temp_file_path)

        # Guard: Ensure output
        if not message_decoded:
            logger.error("Failed to decode audio")
            raise HTTPException(status_code=400, detail="Failed to decode audio")

        # Get chat response
        chat_response = get_chat_response(message_decoded)
        logger.info("Chat response: %s", chat_response)

        # Store messages
        store_messages(message_decoded, chat_response)

        # Guard: Ensure output
        if not chat_response:
            logger.error("Failed chat response")
            raise HTTPException(status_code=400, detail="Failed chat response")

        # Convert chat response to audio
        audio_output = convert_text_to_speech(chat_response)
        logger.info("Audio output generated")

        # Guard: Ensure output
        if not audio_output:
            logger.error("Failed audio output")
            raise HTTPException(status_code=400, detail="Failed audio output")

        # Create a generator that yields chunks of data
        def iterfile():
            yield audio_output

        # Use for Post: Return output audio
        return StreamingResponse(iterfile(), media_type="application/octet-stream")

    except Exception as e:
        logger.exception("An error occurred: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal Server Error")