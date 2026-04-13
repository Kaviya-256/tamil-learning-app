from elevenlabs.client import ElevenLabs
from elevenlabs.play import play
import os
import uuid

from dotenv import load_dotenv

load_dotenv()

UPLOAD_DIR_AUDIO = 'asset/audio'


client = ElevenLabs(
    api_key=os.getenv('ELEVENLABS_APIKEY')
)

def generate_audio(text: str):
    
    audio_name=f'{text}_{uuid.uuid4()}.mp3'
    
    audio_path=os.path.join(UPLOAD_DIR_AUDIO, audio_name)
    
    
    audio = client.text_to_speech.convert(
        text=text,
        voice_id="9TwzC887zQyDD4yBthzD",
        model_id="eleven_multilingual_v2",
        output_format="mp3_44100_128",
    )

    with open(audio_path,'wb') as f:
        # if isinstance(audio, bytes):
        #     f.write(audio)
        #     print('yes')
            
        # else:
            for chunk in audio:
                print('no')
                f.write(chunk)

    return audio_path