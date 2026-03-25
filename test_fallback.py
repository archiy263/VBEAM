from modules.gemini_ai import normalize_phonetic
import sys

print("Normalizing STT string...")
input_text = "एआरसीएचईईडीईएबीएटदरेट263gmail.com@gmail.com"
out = normalize_phonetic(input_text)
print("Input:", input_text)
print("Output:", out)

input_2 = "एट द रेट देव उपाध्याय ऑफिशियल"
print("Input 2:", input_2)
print("Output:", normalize_phonetic(input_2))
