
import pyttsx3
import time

print("Initializing Loop...")
engine = pyttsx3.init()
voices = engine.getProperty('voices')
print(f"Loaded {len(voices)} voices.")


print("Speaking...")
engine.setProperty('rate', 300)
engine.say("This is a test of the emergency broadcast system.", "reading")
engine.runAndWait()
print("Done.")
