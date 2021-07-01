from gtts import gTTS
from io import BytesIO

#wav_fp = BytesIO()

# tts = gTTS( text='현재 상태를 입력해주세요', lang='ko', slow=False )
# #tts.write_to_fp(wav_fp)
# tts.save('in.wav')
# tts1 = gTTS( text='입력이 완료 되었습니다', lang='ko', slow=False )
# tts1.save('out.wav')

tts1 = gTTS( text='입력이 지연되어 무응답 상태로 입력합니다', lang='ko', slow=False )
tts1.save('no_answer.wav')