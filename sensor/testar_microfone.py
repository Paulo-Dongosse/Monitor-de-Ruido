import sounddevice as sd
import numpy as np
import time

DEVICE_ID = 22  # <- microfone correto detectado
DURATION = 1    # segundos
SAMPLE_RATE = 44100

print("=== Monitor de Ruído Local ===")
print("🎤 Capturando som em tempo real... (Ctrl+C para parar)")

try:
    while True:
        audio = sd.rec(int(DURATION * SAMPLE_RATE),
                       samplerate=SAMPLE_RATE,
                       channels=1,
                       dtype='float32',
                       device=DEVICE_ID)
        sd.wait()

        audio = np.nan_to_num(audio)
        rms = np.sqrt(np.mean(audio ** 2))
        db = 20 * np.log10(rms + 1e-6)

        print(f"Nível de ruído: {db:.2f} dB")
        time.sleep(1)

except KeyboardInterrupt:
    print("\n🛑 Monitoramento encerrado.")
