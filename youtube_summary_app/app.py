# app.py
import os
import traceback
from flask import Flask, render_template, request, jsonify
import openai
from urllib.parse import parse_qs, urlparse
import requests
from gtts import gTTS
import base64
import io
from pydub import AudioSegment
from pydub.playback import play
from moviepy.editor import AudioFileClip, ImageClip, ImageSequenceClip
from moviepy.video.fx import all as vfx
from PIL import Image
from moviepy.editor import vfx
from PIL import Image
from PIL import ImageFilter
from moviepy.editor import ImageClip, VideoFileClip
from moviepy.editor import ImageSequenceClip, AudioFileClip
import numpy as np
import cv2

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        video_url = request.form.get('videoURL')

        # Call YouTube API to get subtitles (you need to implement this)
        subtitles = get_subtitles(video_url)
        print("subtitles", subtitles)

        # Combine subtitles into a single string
        text_summary = ' '.join(subtitles)

        # Call ChatGPT API for text summarization (you need to implement this)
        audio_summary = summarize_text(text_summary)
        print("Generated Summary:", audio_summary)

        # Convert text summary to audio (you need to implement this)
        base64_audio = text_to_speech(audio_summary)
        output_path = os.path.join('static', 'output.mp4')  # Replace with your output path
        # Create summary video (you need to implement this)
        image_folder = os.path.join('static', 'images')  # Replace with your image folder
        
        base64_video = create_summary_video(base64_audio, image_folder, output_path)

        # return jsonify({'base64Video': base64_video, 'base64Audio': base64_audio})
        return jsonify({'base64Video': [base64_audio, image_folder, output_path], 'base64Audio': base64_audio})


    return render_template('index.html')

def get_subtitles(video_url):
    parsed_url = urlparse(video_url)
    query_parameters = parse_qs(parsed_url.query)

    video_id = query_parameters.get('v', [''])[0]

    print("Extracted Video ID:", video_id)

    if not video_id:
        # Handle the case where video ID is not found
        return []

    # Make a Google API call to get captions (replace YOUR_GOOGLE_API_KEY with your actual API key)
    google_api_key = 'AIzaSyC9qrDd7hMWinffcA78WmqlYQq9cm8NzRQ'
    captions_url = f'https://www.googleapis.com/youtube/v3/captions?part=snippet&videoId={video_id}&key={google_api_key}'
    
    try:
        response = requests.get(captions_url)
        response.raise_for_status()
        captions_data = response.json()

        # Extract captions from the response (modify this based on the actual response structure)
        subtitles = [item['snippet']['textOriginal'] for item in captions_data.get('items', [])]

        print("Generated Subtitles:")
        for subtitle in subtitles:
            print(subtitle)

        # return subtitles
        return ["hackathon", "guidlines"]

    except requests.exceptions.RequestException as e:
        # Handle API request errors
        print(f"Error fetching captions: {e}")
        print(f"Response content: {response.content if 'response' in locals() else ''}")
        return ["hackathon", "guidlines"]
        # return []


def summarize_text(text):
    openai.api_key = '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'

    try:
        # Make the ChatGPT API call for text summarization
        response = openai.Completion.create(
            engine="text-davinci-003",  # Choose the appropriate engine
            prompt=text,
            max_tokens=150,  # Adjust as needed
            temperature=0.7,  # Adjust as needed
        )

        # Extract the generated summary from the API response
        summary = response.choices[0].text.strip()
        
        summary = "The maximum team size is capped at 4 members while there is no minimum team size"
        return summary

    except Exception as e:
        # Handle API request errors
        print(f"Error summarizing text: {e}")
        # return None
        summary = "The maximum team size is capped at 4 members while there is no minimum team size "
        return summary

def text_to_speech(text):
    try:
        # Create a gTTS object
        tts = gTTS(text=text, lang='en')  # You can specify the language

        # Save the audio to a BytesIO buffer
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)

        # Convert the BytesIO buffer to base64
        base64_audio = base64.b64encode(audio_buffer.getvalue()).decode('utf-8')

        # Play the audio
        # play(AudioSegment.from_file(audio_buffer, format="mp3"))

        return base64_audio

    except Exception as e:
        # Handle errors during text-to-speech conversion
        print(f"Error converting text to speech: {e}")
        return None


def create_summary_video(base64_audio, image_folder, output_path):
    try:
        # Decode base64 audio
        audio_data = base64.b64decode(base64_audio)

        # Save the audio to a file
        audio_path = 'static/audio_summary.mp3'
        with open(audio_path, 'wb') as audio_file:
            audio_file.write(audio_data)

        print("Audio saved to:", audio_path)

        # Load the audio clip
        audio_clip = cv2.VideoCapture(audio_path)

        # Get the list of image files in the specified folder
        image_files = [f for f in os.listdir(image_folder) if f.endswith(('.png', '.jpg', '.jpeg'))]

        # Sort image files based on their names (you may need to adjust this based on your naming convention)
        image_files.sort()

        # Create a VideoWriter object
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # You may need to adjust the codec based on your system

        # Get the dimensions of the first image in the folder
        first_image_path = os.path.join(image_folder, image_files[0])
        first_image = cv2.imread(first_image_path)
        frame_height, frame_width, _ = first_image.shape

        video_writer = cv2.VideoWriter(output_path, fourcc, audio_clip.get(cv2.CAP_PROP_FPS), (frame_width, frame_height))

        # Iterate through image files and write frames to the video
        for image_file in image_files:
            image_path = os.path.join(image_folder, image_file)
            frame = cv2.imread(image_path)
            video_writer.write(frame)

        # Release the video writer
        video_writer.release()

        print("Video created successfully:", output_path)

        return output_path

    except Exception as e:
        traceback.print_exc()
        # Handle errors during video creation
        print(f"Error creating video: {e}")
        return None



if __name__ == '__main__':
    app.run(debug=True)
