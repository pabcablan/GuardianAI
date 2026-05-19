"""Settings and option metadata for anonymization prompts."""

DEFAULT_ANONYMIZATION_SETTINGS = {
    "personNames": "anonymize",
    "identityDocuments": "anonymize",
    "emails": "anonymize",
    "addresses": "anonymize",
    "phones": "anonymize",
    "licensePlates": "anonymize",
    "organizations": "anonymize",
    "relevantCodes": "anonymize",
}


ANONYMIZATION_OPTION_SPECS = [
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
        "licensePlates",
        "CODIGO",
        "Matriculas de vehiculos y otros identificadores similares.",
    ),
    (
        "addresses",
        "DIR",
        "Calles, vias, codigos postales de 5 digitos, municipios, localidades, islas y paises.",
    ),
    (
        "relevantCodes",
        "CODIGO",
        "Expedientes, localizadores, CSV, numeros de registro y codigos alfanumericos sensibles, incluidos identificadores largos con guiones, barras o guiones bajos.",
    ),
]

OUTPUT_KEY_ORDER = ["NOMBRE", "DOC", "CONTACTO", "DIR", "CODIGO"]


def normalize_anonymization_settings(
    settings: dict[str, str] | None,
) -> dict[str, str]:
    """Normalize UI settings and fill in any missing categories."""
    normalized = dict(DEFAULT_ANONYMIZATION_SETTINGS)
    if not settings:
        return normalized

    for key, value in settings.items():
        if key in normalized and value in {"anonymize", "keep"}:
            normalized[key] = value

    return normalized


def should_anonymize_anything(settings: dict[str, str] | None) -> bool:
    """Return whether at least one category is enabled for anonymization."""
    normalized = normalize_anonymization_settings(settings)
    return any(value == "anonymize" for value in normalized.values())
