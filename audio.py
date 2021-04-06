import pyaudio
import numpy as np
from scipy.io.wavfile import write

def get_audio(FORMAT=pyaudio.paInt16, RATE = 44100, CHANNELS = 1, CHUNK = 1, duration = 5) :
    p = pyaudio.PyAudio()
    
    stream = p.open(
            format = FORMAT,
            rate = RATE,
            channels = CHANNELS,
            input = True,
            frames_per_buffer = CHUNK
            )

    data = []
    flag = False

    for i in range(int(duration * RATE / CHUNK)) :
        frame = np.fromstring(stream.read(CHUNK), dtype = np.int16)

        if not flag : 
            data = frame

        else :
            data = np.concatenate((data, frame), axis = None)

        flag = True

    stream.stop_stream()
    stream.close()
    p.terminate()

    return data

def save_wav(data, save_path = './record.wav', RATE = 44100) : 
    write(save_path, RATE, data.astype(np.int16))


if __name__ == '__main__' :
    data = get_audio()
    print(data)
    save_wav(data) 
