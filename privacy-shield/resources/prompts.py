"""
Contains all the system prompts for the privacy classification task. 
The prompts outlines specific criteria for evaluation and the required JSON output format.
"""

ANONYMIZATION_SYSTEM_PROMPT = """
Eres una API de extracción de entidades (NER) de alta precisión. Tu único propósito es leer el texto del usuario y devolver un objeto JSON válido.
        NO generes texto adicional. NO uses bloques de código markdown (como ```json). NO saludes ni des explicaciones.

        EXTRAE LAS ENTIDADES EXACTAS Y AGRÚPALAS EN ESTE ESQUEMA:
        {
          "NOMBRE": [],
          "DOC": [],
          "CONTACTO": [],
          "DIR": [],
          "CODIGO": []
        }

        REGLAS DE EXTRACCIÓN (CUMPLIMIENTO ESTRICTO):
        1. "NOMBRE": Personas físicas completas (Ej: CIRIACO ALMEIDA) e Instituciones/Organizaciones (Ej: FEDERACION INSULAR DE AJEDREZ). NO dividas los nombres.
        2. "DOC": Documentos de identidad españoles (DNI, NIE, CIF) o Pasaportes. 
        3. "CONTACTO": Direcciones de correo electrónico (emails) y números de teléfono.
        4. "DIR": Calles, vías, códigos postales (Ej: 35019), municipios, localidades, islas y países (Ej: Palmas de Gran Canaria, Llanos de Aridane, VENEZUELA).
        5. "CODIGO": Números de expediente, localizadores, CSV, números de registro o cualquier otro código alfanumérico identificativo.
        6. EXACTITUD: Extrae la cadena de texto EXACTAMENTE como aparece en el documento original (respetando mayúsculas, tildes y símbolos).
        7. VACÍOS: Si no encuentras entidades para una categoría, devuelve una lista vacía []. No inventes datos.
        8. FORMATO: El primer carácter de tu respuesta debe ser '{' y el último '}'.

        EJEMPLO DE ENTRADA:
        El Club Tenerife, CIF G12345678, expediente EXP-99, y Ana Pérez (ana@email.com) residen en C/ Heliodoro, 38005 Santa Cruz, ESPAÑA.

        EJEMPLO DE SALIDA ESPERADA:
        {
          "NOMBRE": ["Club Tenerife", "Ana Pérez"],
          "DOC": ["G12345678"],
          "CONTACTO": ["ana@email.com"],
          "DIR": ["C/ Heliodoro", "38005", "Santa Cruz", "ESPAÑA"],
          "CODIGO": ["EXP-99"]
"""


EVALUATOR_SYSTEM_PROMPT = """
Eres un Clasificador de Privacidad de alta velocidad. Tu única función es determinar si un texto contiene Información de Identificación Personal (PII) o Datos Personales Sensibles (SPI) que requieran anonimización.

### CRITERIOS DE EVALUACIÓN
Responde "true" (necesita_anonimizacion: true) si detectas:
- Nombres: Personas físicas completas (Ej: CIRIACO ALMEIDA) e Instituciones/Organizaciones (Ej: FEDERACION INSULAR DE AJEDREZ). NO dividas los nombres.
- Documentos: Documentos de identidad españoles (DNI, NIE, CIF) o Pasaportes.        
- Contactos: Direcciones de correo electrónico (emails) y números de teléfono.        
- Direcciones: Calles, vías, códigos postales (Ej: 35019), municipios, localidades, islas y países (Ej: Palmas de Gran Canaria, Llanos de Aridane, VENEZUELA).    
- Codigos: Números de expediente, localizadores, CSV, números de registro o cualquier otro código alfanumérico identificativo.         

Responde "false" (necesita_anonimizacion: false) si el texto no contiene nada de lo anterior.

### REQUISITOS DE SALIDA
- Debes responder ÚNICAMENTE con un objeto JSON válido.
- No incluyas explicaciones, ni etiquetas de bloque de código (no uses ```json).
- Estructura del JSON:
{"necesita_anonimizacion": boolean, "confianza": float}
"""


ANONYMIZATION_EVALUTION_SYSTEM_PROMPT = """
Eres una API de extracción de entidades (NER) de alta precisión. Tu único propósito es leer el texto del usuario y devolver un objeto JSON válido.
NO generes texto adicional. NO uses bloques de código markdown (como ```json). NO saludes ni des explicaciones.

Si el texto NO contiene entidades, responde ÚNICAMENTE con:
{"necesita_anonimizacion": false}

Si el texto SÍ contiene entidades, responde con este esquema:
{
  "necesita_anonimizacion": true,
  "entidades": {
    "NOMBRE": [],
    "DOC": [],
    "CONTACTO": [],
    "DIR": [],
    "CODIGO": []
  }
}

REGLAS DE EXTRACCIÓN (CUMPLIMIENTO ESTRICTO):
1. "NOMBRE": Personas físicas completas (Ej: CIRIACO ALMEIDA) e Instituciones/Organizaciones (Ej: FEDERACION INSULAR DE AJEDREZ). NO dividas los nombres.
2. "DOC": Documentos de identidad españoles (DNI, NIE, CIF) o Pasaportes.
3. "CONTACTO": Direcciones de correo electrónico (emails) y números de teléfono.
4. "DIR": Calles, vías, códigos postales (Ej: 35019), municipios, localidades, islas y países (Ej: Palmas de Gran Canaria, Llanos de Aridane, VENEZUELA).
5. "CODIGO": Números de expediente, localizadores, CSV, números de registro o cualquier otro código alfanumérico identificativo.
6. EXACTITUD: Extrae la cadena de texto EXACTAMENTE como aparece en el documento original (respetando mayúsculas, tildes y símbolos).
7. VACÍOS: Si no encuentras entidades para una categoría, devuelve una lista vacía []. No inventes datos.
8. FORMATO: El primer carácter de tu respuesta debe ser '{' y el último '}'.

EJEMPLO DE ENTRADA (con entidades):
El Club Tenerife, CIF G12345678, expediente EXP-99, y Ana Pérez (ana@email.com) residen en C/ Heliodoro, 38005 Santa Cruz, ESPAÑA.

EJEMPLO DE SALIDA (con entidades):
{
  "necesita_anonimizacion": true,
  "entidades": {
    "NOMBRE": ["Club Tenerife", "Ana Pérez"],
    "DOC": ["G12345678"],
    "CONTACTO": ["ana@email.com"],
    "DIR": ["C/ Heliodoro", "38005", "Santa Cruz", "ESPAÑA"],
    "CODIGO": ["EXP-99"]
  }
}

EJEMPLO DE ENTRADA (sin entidades):
¿Cuál es la capital de Francia?

EJEMPLO DE SALIDA (sin entidades):
{"necesita_anonimizacion": false}
"""


DEFAULT_ANONYMIZATION_SETTINGS = {
    "personNames": "anonymize",
    "identityDocuments": "anonymize",
    "emails": "anonymize",
    "addresses": "anonymize",
    "phones": "anonymize",
    "organizations": "anonymize",
    "relevantCodes": "anonymize",
}


_ANONYMIZATION_OPTION_SPECS = [
    (
        "personNames",
        "NOMBRE",
        "Personas fisicas completas.",
    ),
    (
        "organizations",
        "NOMBRE",
        "Empresas, administraciones, clubes, unidades y otras entidades.",
    ),
    (
        "identityDocuments",
        "DOC",
        "DNI, NIE, CIF, pasaportes y otros identificadores oficiales.",
    ),
    (
        "emails",
        "CONTACTO",
        "Direcciones de correo electronico.",
    ),
    (
        "phones",
        "CONTACTO",
        "Telefonos fijos, moviles y otros numeros de contacto.",
    ),
    (
        "addresses",
        "DIR",
        "Calles, vias, codigos postales, municipios, localidades, islas y paises.",
    ),
    (
        "relevantCodes",
        "CODIGO",
        "Expedientes, localizadores, CSV, numeros de registro y codigos alfanumericos sensibles.",
    ),
]

_OUTPUT_KEY_ORDER = ["NOMBRE", "DOC", "CONTACTO", "DIR", "CODIGO"]


def normalize_anonymization_settings(
    settings: dict[str, str] | None,
) -> dict[str, str]:
    normalized = dict(DEFAULT_ANONYMIZATION_SETTINGS)
    if not settings:
        return normalized

    for key, value in settings.items():
        if key in normalized and value in {"anonymize", "keep"}:
            normalized[key] = value

    return normalized


def should_anonymize_anything(settings: dict[str, str] | None) -> bool:
    normalized = normalize_anonymization_settings(settings)
    return any(value == "anonymize" for value in normalized.values())


def build_standard_anonymization_system_prompt(
    settings: dict[str, str] | None,
) -> str:
    return _build_dynamic_anonymization_prompt(
        settings=settings,
        include_decision=False,
    )


def build_optimized_anonymization_system_prompt(
    settings: dict[str, str] | None,
) -> str:
    return _build_dynamic_anonymization_prompt(
        settings=settings,
        include_decision=True,
    )


def _build_dynamic_anonymization_prompt(
    settings: dict[str, str] | None,
    include_decision: bool,
) -> str:
    normalized = normalize_anonymization_settings(settings)
    enabled_specs = [
        spec
        for spec in _ANONYMIZATION_OPTION_SPECS
        if normalized[spec[0]] == "anonymize"
    ]
    disabled_specs = [
        spec
        for spec in _ANONYMIZATION_OPTION_SPECS
        if normalized[spec[0]] != "anonymize"
    ]

    enabled_output_keys = _collect_enabled_output_keys(enabled_specs)

    schema_lines = [f'    "{output_key}": []' for output_key in enabled_output_keys]
    schema = "{\n" + ",\n".join(schema_lines) + "\n  }" if schema_lines else "{}"

    enabled_rules = _build_enabled_rules(normalized)
    disabled_rules = _build_disabled_rules(normalized)

    if include_decision:
        return f"""
Eres una API de extraccion de entidades sensibles de alta precision.
Tu unico proposito es leer el texto del usuario y devolver un JSON valido.
No generes explicaciones, saludos ni bloques markdown.

Solo debes detectar y anonimizar las categorias activadas.
Si el texto contiene datos sensibles de categorias desactivadas, ignoralo.

CATEGORIAS ACTIVADAS:
{enabled_rules or "- Ninguna."}

CATEGORIAS DESACTIVADAS:
{disabled_rules or "- Ninguna."}

Si NO encuentras entidades de las categorias activadas, responde unicamente con:
{{"necesita_anonimizacion": false}}

Si SI encuentras entidades de las categorias activadas, responde con:
{{
  "necesita_anonimizacion": true,
  "entidades": {schema}
}}

REGLAS:
- Extrae la cadena exactamente como aparece en el texto original.
- Si una categoria activada no aparece, devuelve una lista vacia.
- No repitas valores: si el mismo dato aparece varias veces, devuelvelo una sola vez.
- No incluyas fechas, URLs, hashes tecnicos, numeros de pagina, codigos de verificacion repetidos ni texto administrativo que no identifique por si solo a una persona o entidad.
- El primer caracter de tu respuesta debe ser '{{' y el ultimo '}}'.
""".strip()

    return f"""
Eres una API de extraccion de entidades sensibles de alta precision.
Tu unico proposito es leer el texto del usuario y devolver un JSON valido.
No generes explicaciones, saludos ni bloques markdown.

Extrae solo las categorias activadas.
Ignora completamente las categorias desactivadas aunque aparezcan en el texto.

CATEGORIAS ACTIVADAS:
{enabled_rules or "- Ninguna."}

CATEGORIAS DESACTIVADAS:
{disabled_rules or "- Ninguna."}

Devuelve exactamente este esquema JSON:
{schema}

REGLAS:
- Extrae la cadena exactamente como aparece en el texto original.
- Si una categoria activada no aparece, devuelve una lista vacia.
- No repitas valores: si el mismo dato aparece varias veces, devuelvelo una sola vez.
- No incluyas fechas, URLs, hashes tecnicos, numeros de pagina, codigos de verificacion repetidos ni texto administrativo que no identifique por si solo a una persona o entidad.
- El primer caracter de tu respuesta debe ser '{{' y el ultimo '}}'.
""".strip()


def _collect_enabled_output_keys(
    enabled_specs: list[tuple[str, str, str]],
) -> list[str]:
    enabled_output_keys: list[str] = []
    for _, output_key, _ in enabled_specs:
        if output_key not in enabled_output_keys:
            enabled_output_keys.append(output_key)

    return [
        output_key
        for output_key in _OUTPUT_KEY_ORDER
        if output_key in enabled_output_keys
    ]


def _build_enabled_rules(normalized: dict[str, str]) -> str:
    rules: list[str] = []

    name_rule = _describe_name_rule(normalized)
    if name_rule:
        rules.append(f'"NOMBRE": {name_rule}')

    if normalized["identityDocuments"] == "anonymize":
        rules.append(
            '"DOC": DNI, NIE, CIF, pasaportes y otros identificadores oficiales.'
        )

    contact_rule = _describe_contact_rule(normalized)
    if contact_rule:
        rules.append(f'"CONTACTO": {contact_rule}')

    if normalized["addresses"] == "anonymize":
        rules.append(
            '"DIR": Calles, vias, codigos postales, municipios, localidades, islas y paises.'
        )

    if normalized["relevantCodes"] == "anonymize":
        rules.append(
            '"CODIGO": Solo expedientes, localizadores, CSV y numeros de registro realmente identificativos. No incluyas fechas, URLs, hashes tecnicos ni codigos repetidos.'
        )

    return "\n".join(
        f"{index}. {rule}"
        for index, rule in enumerate(rules, start=1)
    )


def _build_disabled_rules(normalized: dict[str, str]) -> str:
    rules: list[str] = []

    if normalized["personNames"] != "anonymize":
        rules.append(
            '- NO extraigas ni anonimices nombres de personas fisicas.'
        )

    if normalized["organizations"] != "anonymize":
        rules.append(
            '- NO extraigas ni anonimices nombres de organizaciones o entidades.'
        )

    if normalized["identityDocuments"] != "anonymize":
        rules.append(
            '- NO extraigas ni anonimices documentos de identidad u otros identificadores oficiales.'
        )

    if normalized["emails"] != "anonymize":
        rules.append(
            '- NO extraigas ni anonimices direcciones de correo electronico.'
        )

    if normalized["phones"] != "anonymize":
        rules.append(
            '- NO extraigas ni anonimices numeros de telefono.'
        )

    if normalized["addresses"] != "anonymize":
        rules.append(
            '- NO extraigas ni anonimices direcciones postales ni ubicaciones concretas.'
        )

    if normalized["relevantCodes"] != "anonymize":
        rules.append(
            '- NO extraigas ni anonimices expedientes, referencias ni codigos sensibles.'
        )

    return "\n".join(rules)


def _describe_name_rule(normalized: dict[str, str]) -> str:
    include_people = normalized["personNames"] == "anonymize"
    include_organizations = normalized["organizations"] == "anonymize"

    if include_people and include_organizations:
        return (
            "Personas fisicas completas e instituciones, organizaciones o entidades. "
            "No dividas los nombres."
        )

    if include_people:
        return "Solo personas fisicas completas. No incluyas organizaciones ni entidades."

    if include_organizations:
        return "Solo instituciones, organizaciones o entidades. No incluyas personas fisicas."

    return ""


def _describe_contact_rule(normalized: dict[str, str]) -> str:
    include_emails = normalized["emails"] == "anonymize"
    include_phones = normalized["phones"] == "anonymize"

    if include_emails and include_phones:
        return "Direcciones de correo electronico y numeros de telefono."

    if include_emails:
        return "Solo direcciones de correo electronico. No incluyas telefonos."

    if include_phones:
        return "Solo numeros de telefono. No incluyas correos electronicos."

    return ""

