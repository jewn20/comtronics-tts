from TTS.api import TTS

tts = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2")

text = """Parang rank game lang ang pag-ibig...
kahit anong galing mo,
kung mali ang kakampi mo,
talo ka pa rin."""

tts.tts_to_file(
    text=text,
    speaker_wav="voice.wav",
    language="en",  # gamitin pa rin 'en'
    file_path="output.wav"
)

print("Done!")