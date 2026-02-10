
import pyttsx3
import pythoncom
from PyQt6.QtCore import QObject, pyqtSignal, QThread

class TTSWorker(QObject):
    """
    Worker to handle TTS operations in a separate thread.
    pyttsx3's runAndWait() is blocking, so this is necessary to keep the UI responsive.
    """
    word_spoken = pyqtSignal(int, int) # location, length
    finished = pyqtSignal()
    voices_loaded = pyqtSignal(list)
    
    def __init__(self):
        super().__init__()
        self.engine = None
        self._current_text_offset = 0 
        self.stop_requested = False
        self.current_rate = 200
        
    def set_rate(self, rate):
        """Update rate dynamically."""
        self.current_rate = max(50, min(rate, 600))

    def init_engine(self):
        """Initialize the engine. Must be called in the worker thread."""
        print("DEBUG: TTSWorker.init_engine CALLED")
        try:
            pythoncom.CoInitialize() # Required for SAPI5 in threads
        except Exception as e:
            print(f"DEBUG: CoInitialize failed: {e}")

        if not self.engine:
            try:
                print("DEBUG: Initializing pyttsx3 with sapi5...")
                # Explicitly use sapi5 for Windows stability
                self.engine = pyttsx3.init('sapi5')
                self.engine.connect('started-word', self._on_word)
                # DELETED: finished-utterance connection was causing premature stopping in chunked mode
                print("DEBUG: pyttsx3 initialized successfully.")
                
                # Load voices
                voices = self.engine.getProperty('voices')
                print(f"DEBUG: System voices found: {len(voices)}")
                for i, v in enumerate(voices):
                    print(f"DEBUG: Voice {i}: {v.name} (ID: {v.id})")
                
                # Format for UI: [{'id': id, 'name': name}, ...]
                voice_data = [{'id': v.id, 'name': v.name} for v in voices]
                self.voices_loaded.emit(voice_data)
                
                # Default settings
                self.engine.setProperty('volume', 1.0)
                self.engine.setProperty('rate', 200)
            except Exception as e:
                print(f"TTS Init Error: {e}")

    def _on_word(self, name, location, length):
        """Callback from pyttsx3 when a word is spoken."""
        # location is the character index in the text passed to say()
        # Mapped in logic now
        pass 
        
    def _on_finished(self, name, completed):
        """Callback when speaking is done."""
        pass 

    def say(self, text, voice_id=None, rate=200):
        """Speak text in chunks to allow interruption and updates."""
        print(f"DEBUG: TTSWorker.say start. Text len: {len(text)}")
        try:
            pythoncom.CoInitialize() 
        except: pass
        
        if not self.engine: 
            self.init_engine()
        
        self.stop_requested = False
        
        # 1. Sanitize text (remove emojis/non-BMP chars but keep newlines/tabs)
        clean_text = "".join(c for c in text if ord(c) < 0xFFFF or c in "\n\r\t")
        
        # 2. Smart Chunking for responsiveness and better rate syncing
        import re
        # Split by sentence/clause punctuation first
        raw_chunks = re.split(r'([.!?,\n\r]+)', clean_text)
        speech_chunks = []
        current = ""
        for part in raw_chunks:
            current += part
            if re.search(r'[.!?,\n\r]', part) or len(current) > 80:
                # If still too long, split by words
                if len(current) > 100:
                    words = current.split()
                    sub = []
                    for w in words:
                        sub.append(w)
                        if len(" ".join(sub)) > 60:
                            speech_chunks.append(" ".join(sub))
                            sub = []
                    if sub: speech_chunks.append(" ".join(sub))
                else:
                    speech_chunks.append(current)
                current = ""
        if current.strip(): speech_chunks.append(current)
        
        print(f"DEBUG: Split into {len(speech_chunks)} chunks")
        
        current_offset = 0
        
        try:
             # Apply initial settings
            if voice_id:
                try: 
                    print(f"DEBUG: Setting TTS Voice to: {voice_id}")
                    self.engine.setProperty('voice', voice_id)
                except Exception as ve: 
                    print(f"DEBUG: Voice setting error: {ve}")
            
            # Initial set
            self.current_rate = max(50, min(rate, 600))
            self.engine.setProperty('rate', self.current_rate)
            self.engine.setProperty('volume', 1.0)

            # Cache current settings to avoid expensive COM calls
            last_rate = self.current_rate
            last_voice = voice_id
            
            for chunk in speech_chunks:
                if not chunk.strip(): continue
                
                # Check for stop signal (set via thread-safe flag or slot)
                if self.stop_requested:
                    print("DEBUG: TTS Stop requested")
                    break
                
                # Update settings ONLY if they changed
                try:
                    if self.current_rate != last_rate:
                        self.engine.setProperty('rate', self.current_rate)
                        last_rate = self.current_rate
                    
                    # Volume is rarely changed per chunk, just ensure it's on
                    # self.engine.setProperty('volume', 1.0) 
                    
                    # Changing voice is very expensive/unstable, do NOT do it in loop unless critical
                    # if voice_id and voice_id != last_voice:
                    #     self.engine.setProperty('voice', voice_id)
                    #     last_voice = voice_id
                except: pass
                
                self.current_chunk_offset = current_offset 
                
                try:
                    self.engine.say(chunk) 
                    self.engine.runAndWait() 
                except Exception as e:
                    print(f"DEBUG: Engine Error: {e}")
                    # If engine errors, it might need re-init, best to break
                    break
                
                current_offset += len(chunk)
                
        except Exception as e:
            print(f"TTS Say Error: {e}")
            
        print("DEBUG: TTS Finished Loop")
        self.finished.emit()

    def _on_word(self, name, location, length):
        """Callback from pyttsx3 when a word is spoken."""
        # Sanity check for location as Windows sometimes returns garbage/negative values
        if location < 0 or location > 10000: return
        
        global_loc = getattr(self, 'current_chunk_offset', 0) + location
        self.word_spoken.emit(global_loc, length)

    def stop(self):
        """Stop speaking."""
        print("DEBUG: TTSWorker.stop called")
        self.stop_requested = True
        if self.engine:
            try:
                self.engine.stop()
            except Exception as e:
                print(f"TTS Stop Error: {e}")
