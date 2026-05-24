import type {
  AnonymizationOption,
  AnonymizationSettings,
} from "../types";
import type { AnonymizationMode } from "../types";

interface AnonymizationSettingsPanelProps {
  settings: AnonymizationSettings;
  onChange: (option: AnonymizationOption, mode: AnonymizationMode) => void;
  onClose: () => void;
}

const SETTING_OPTIONS: Array<{
  key: AnonymizationOption;
  label: string;
  description: string;
}> = [
  {
    key: "personNames",
    label: "Nombres propios",
    description: "Personas físicas mencionadas en documentos y mensajes.",
  },
  {
    key: "identityDocuments",
    label: "Documentos de identidad",
    description: "DNI, NIE, pasaportes u otros identificadores oficiales.",
  },
  {
    key: "emails",
    label: "Correos",
    description: "Direcciones de correo electrónico personales o corporativas.",
  },
  {
    key: "addresses",
    label: "Direcciones",
    description: "Direcciones postales, domicilios y ubicaciones concretas.",
  },
  {
    key: "licensePlates",
    label: "Matrículas",
    description: "Matrículas de vehículos y otros identificadores similares.",
  },
  {
    key: "phones",
    label: "Teléfonos",
    description: "Números fijos, móviles y otros datos de contacto telefónico.",
  },
  {
    key: "organizations",
    label: "Organizaciones",
    description: "Empresas, administraciones, unidades y entidades.",
  },
  {
    key: "relevantCodes",
    label: "Códigos relevantes",
    description: "Expedientes, referencias, cuentas u otros códigos sensibles.",
  },
];

// Render the anonymization settings panel used to tune protection rules.
export function AnonymizationSettingsPanel({
  settings,
  onChange,
  onClose,
}: AnonymizationSettingsPanelProps) {
  return (
    <aside className="settings-panel" aria-label="Configuración de anonimización">
      <div className="settings-panel__header">
        <div>
          <p className="settings-panel__eyebrow">Configuración</p>
          <h2>Anonimización</h2>
        </div>
        <button
          className="settings-panel__close"
          type="button"
          onClick={onClose}
          aria-label="Cerrar configuración"
        >
          x
        </button>
      </div>

      <p className="settings-panel__copy">
        Elige qué tipos de información sensible debe ocultar Guardian AI antes
        de continuar el flujo.
      </p>

      <div className="settings-panel__controls">
        {SETTING_OPTIONS.map((option) => (
          <label
            className={`settings-control ${settings[option.key] === "anonymize" ? "settings-control--enabled" : ""}`.trim()}
            key={option.key}
          >
            <input
              className="settings-control__checkbox"
              type="checkbox"
              checked={settings[option.key] === "anonymize"}
              onChange={(event) =>
                onChange(
                  option.key,
                  event.target.checked ? "anonymize" : "keep",
                )
              }
            />
            <span className="settings-control__copy">
              <span className="settings-control__title">
                <span className="settings-control__indicator" aria-hidden="true" />
                <strong>{option.label}</strong>
              </span>
              <span>{option.description}</span>
            </span>
          </label>
        ))}
      </div>
    </aside>
  );
}
