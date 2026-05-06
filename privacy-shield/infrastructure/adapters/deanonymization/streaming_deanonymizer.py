import re
from infrastructure.ports.deanonymizer import Deanonymizer

class StreamingDeanonymizer(Deanonymizer):
    def __init__(self):
        self.buffer = ""
        self.partial_pattern = re.compile(r"\[[A-Z_0-9]*$")

    def deanonymize(self, text: str, replacements: dict[str, str]) -> str:
        self.buffer += text
        
        match = self.partial_pattern.search(self.buffer)
        
        if match:
            punto_de_corte = match.start()
            texto_seguro = self.buffer[:punto_de_corte]
            self.buffer = self.buffer[punto_de_corte:]
        else:
            texto_seguro = self.buffer
            self.buffer = ""

        for tag, original in replacements.items():
            texto_seguro = texto_seguro.replace(tag, original)
            
        return texto_seguro

    def flush(self, replacements: dict[str, str]) -> str:
        restante = self.buffer
        self.buffer = ""
        for tag, original in replacements.items():
            restante = restante.replace(tag, original)
        return restante