"""
Puertos del modulo Web IU.

Aqui se definen los contratos que necesita la capa de aplicacion para
trabajar con el backend del chat sin depender de implementaciones
concretas.

Organizacion:
- `internal/`: puertos propios del modulo para chats, mensajes,
  documentos y streaming
- `external/`: puertos de integracion con otros modulos o servicios
  externos como LLM, procesamiento documental o privacidad
"""
