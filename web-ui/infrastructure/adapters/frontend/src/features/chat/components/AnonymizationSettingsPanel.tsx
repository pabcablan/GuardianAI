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
    description: "Personas fisicas mencionadas en documentos y mensajes.",
  },
  {
    key: "identityDocuments",
    label: "Documentos de identidad",
    description: "DNI, NIE, pasaportes u otros identificadores oficiales.",
  },
  {
    key: "emails",
    label: "Correos",
    description: "Direcciones de correo electronico personales o corporativas.",
  },
  {
    key: "addresses",
    label: "Direcciones",
    description: "Direcciones postales, domicilios y ubicaciones concretas.",
  },
  {
    key: "phones",
    label: "Telefonos",
    description: "Numeros fijos, moviles y otros datos de contacto telefonico.",
  },
  {
    key: "organizations",
    label: "Organizaciones",
    description: "Empresas, administraciones, unidades y entidades.",
  },
  {
    key: "relevantCodes",
    label: "Codigos relevantes",
    description: "Expedientes, referencias, cuentas u otros codigos sensibles.",
  },
];

export function AnonymizationSettingsPanel({
  settings,
  onChange,
  onClose,
}: AnonymizationSettingsPanelProps) {
  return (
    <aside className="settings-panel" aria-label="Configuracion de anonimizacion">
      <div className="settings-panel__header">
        <div>
          <p className="settings-panel__eyebrow">Configuracion</p>
          <h2>Anonimizacion</h2>
        </div>
        <button
          className="settings-panel__close"
          type="button"
          onClick={onClose}
          aria-label="Cerrar configuracion"
        >
          x
        </button>
      </div>

      <p className="settings-panel__copy">
        Elige que tipos de informacion sensible debe ocultar Guardian AI antes
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
            <span className="settings-control__indicator" aria-hidden="true" />
            <span className="settings-control__copy">
              <strong>{option.label}</strong>
              <span>{option.description}</span>
            </span>
            <span className="settings-control__state">
              {settings[option.key] === "anonymize" ? "Anonimizar" : "Conservar"}
            </span>
          </label>
        ))}
      </div>
    </aside>
  );
}
