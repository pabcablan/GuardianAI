"""Prompt builder for the active anonymization flow."""

from resources.anonymization_settings import (
    ANONYMIZATION_OPTION_SPECS,
    OUTPUT_KEY_ORDER,
    normalize_anonymization_settings,
)


def build_optimized_anonymization_system_prompt(
    settings: dict[str, str] | None,
) -> str:
    """Build the single-pass anonymization prompt used by the live flow."""
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
        for spec in ANONYMIZATION_OPTION_SPECS
        if normalized[spec[0]] == "anonymize"
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
- Ignora valores ya parcial o totalmente ofuscados, enmascarados o redacted, por ejemplo cadenas con asteriscos como "***3691**".
- No incluyas fechas, URLs, hashes tecnicos, numeros de pagina, codigos de verificacion repetidos ni texto administrativo que no identifique por si solo a una persona o entidad.
- En "CODIGO", devuelve como maximo 5 valores unicos y prioriza los mas relevantes.
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
- Ignora valores ya parcial o totalmente ofuscados, enmascarados o redacted, por ejemplo cadenas con asteriscos como "***3691**".
- No incluyas fechas, URLs, hashes tecnicos, numeros de pagina, codigos de verificacion repetidos ni texto administrativo que no identifique por si solo a una persona o entidad.
- En "CODIGO", devuelve como maximo 5 valores unicos y prioriza los mas relevantes.
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
        for output_key in OUTPUT_KEY_ORDER
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
            '"DIR": Calles, vias, codigos postales de 5 digitos, municipios, localidades, islas y paises. Incluye siempre codigos postales cuando aparezcan como parte de una direccion o ubicacion postal. En texto OCR o formularios linealizados, captura tambien valores que aparezcan tras etiquetas como LOCALIDAD, DOMICILIO, MUNICIPIO, PROVINCIA o DIRECCION.'
        )

    code_rule = _describe_code_rule(normalized)
    if code_rule:
        rules.append(f'"CODIGO": {code_rule}')

    return "\n".join(
        f"{index}. {rule}"
        for index, rule in enumerate(rules, start=1)
    )


def _build_disabled_rules(normalized: dict[str, str]) -> str:
    rules: list[str] = []

    if normalized["personNames"] != "anonymize":
        rules.append('- NO extraigas ni anonimices nombres de personas fisicas.')

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
        rules.append('- NO extraigas ni anonimices numeros de telefono.')

    if normalized["addresses"] != "anonymize":
        rules.append(
            '- NO extraigas ni anonimices direcciones postales ni ubicaciones concretas.'
        )

    if normalized["licensePlates"] != "anonymize":
        rules.append(
            '- NO extraigas ni anonimices matriculas ni identificadores de vehiculos.'
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
            "No dividas los nombres. Si en tablas aparecen nombre y apellidos en celdas o lineas consecutivas, reconstruye el nombre completo. "
            "En texto OCR o formularios linealizados, si aparecen etiquetas como NOMBRE FEDERACION, NOMBRE DE LA ENTIDAD, NOMBRE/RAZON SOCIAL, INTERESADO o TITULAR, extrae el nombre completo que siga a la etiqueta y detenlo antes del siguiente campo administrativo."
        )

    if include_people:
        return (
            "Solo personas fisicas completas. No incluyas organizaciones ni entidades. "
            "Si en tablas aparecen nombre y apellidos en celdas o lineas consecutivas, reconstruye el nombre completo."
        )

    if include_organizations:
        return (
            "Solo instituciones, organizaciones o entidades. No incluyas personas fisicas. "
            "En texto OCR o formularios linealizados, si aparecen etiquetas como NOMBRE FEDERACION, NOMBRE DE LA ENTIDAD o NOMBRE/RAZON SOCIAL, extrae el nombre completo que siga a la etiqueta y detenlo antes del siguiente campo administrativo."
        )

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


def _describe_code_rule(normalized: dict[str, str]) -> str:
    include_license_plates = normalized["licensePlates"] == "anonymize"
    include_relevant_codes = normalized["relevantCodes"] == "anonymize"

    if include_license_plates and include_relevant_codes:
        return (
            "Expedientes, localizadores, CSV, numeros de registro, matriculas "
            "de vehiculos y otros codigos alfanumericos identificativos, aunque "
            "sean largos o contengan guiones, barras o guiones bajos. Incluye "
            "identificadores como NDE, UUID o cadenas similares cuando funcionen "
            "como referencia del documento. Ignora valores ya ofuscados o "
            "parcialmente tapados con asteriscos. No incluyas fechas ni URLs "
            "completas. Devuelve como maximo 5 codigos unicos y prioriza los "
            "mas relevantes."
        )

    if include_relevant_codes:
        return (
            "Solo expedientes, localizadores, CSV, numeros de registro y otros "
            "codigos alfanumericos identificativos, aunque sean largos o "
            "contengan guiones, barras o guiones bajos. Incluye identificadores "
            "como NDE, UUID o cadenas similares cuando funcionen como referencia "
            "del documento. Ignora valores ya ofuscados o parcialmente tapados "
            "con asteriscos. No incluyas matriculas, fechas ni URLs completas. "
            "Devuelve como maximo 5 codigos unicos y prioriza los mas relevantes."
        )

    if include_license_plates:
        return (
            "Solo matriculas de vehiculos, incluidas matriculas modernas y "
            "antiguas, con o sin espacios o guiones. No incluyas otros "
            "expedientes ni referencias."
        )

    return ""
