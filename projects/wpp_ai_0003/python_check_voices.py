import pyttsx3

engine = pyttsx3.init()
voices = engine.getProperty('voices')

print("Vozes disponíveis no sistema:")
for i, voice in enumerate(voices):
    print(f"--- Voz {i} ---")
    print(f"ID: {voice.id}")
    print(f"Nome: {voice.name}")
    print(f"Idiomas: {voice.languages}")
    print(f"Gênero: {voice.gender}")
    print(f"Idade: {voice.age}")
    print("-" * 20)

# Tente encontrar uma voz em português
portuguese_voice_id = None
for voice in voices:
    # 'pt-br' ou 'pt_BR' são os mais comuns para português brasileiro
    # Alguns sistemas podem ter apenas 'pt'
    if 'pt-br' in [lang.decode('utf-8') for lang in voice.languages] or \
       'pt_BR' in [lang.decode('utf-8') for lang in voice.languages] or \
       'pt' in [lang.decode('utf-8') for lang in voice.languages] or \
       'brazil' in voice.name.lower() or 'portugues' in voice.name.lower(): # Verificação mais flexível
        portuguese_voice_id = voice.id
        print(f"\n### Voz em português encontrada! ID: {portuguese_voice_id}, Nome: {voice.name} ###")
        break

if not portuguese_voice_id:
    print("\nNenhuma voz em português brasileiro (pt-br) ou português (pt) detectada. Por favor, instale uma.")
    print("Para sistemas Linux (Ubuntu/Debian), você pode tentar instalar 'espeak-ng' ou 'festival'.")
    print("Para uma voz mais natural em Linux, 'mimic' ou 'flite' com pacotes de voz específicos podem ser necessários, ou usar serviços em nuvem.")
    print("No Windows, verifique as configurações de 'Voz' para adicionar pacotes de idioma.")

# Exemplo de teste com uma voz, se encontrada (opcional)
if portuguese_voice_id:
    engine.setProperty('voice', portuguese_voice_id)
    engine.say("Olá, esta é uma voz de teste em português.")
    engine.runAndWait()

engine.stop()