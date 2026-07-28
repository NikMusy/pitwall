// Minimal typed dictionary. A real i18n library earns its place when we have
// plurals and interpolation to worry about; right now it would be weight
// without benefit.

export const LANGUAGES = ['ru', 'en'] as const;
export type Language = (typeof LANGUAGES)[number];

export const DEFAULT_LANGUAGE: Language = 'ru';

const STRINGS = {
  appName: { ru: 'PitWall', en: 'PitWall' },
  noAgent: {
    ru: 'Агент не подключён',
    en: 'No agent connected',
  },
  noAgentHint: {
    ru: 'Телеметрии нет. Запустите агент на ПК пилота.',
    en: 'No telemetry. Start the agent on the driver’s PC.',
  },
  channelsKnown: { ru: 'Каналов в схеме', en: 'Channels in schema' },
  protocolVersion: { ru: 'Версия протокола', en: 'Protocol version' },
  milestone: { ru: 'Веха', en: 'Milestone' },
} as const satisfies Record<string, Record<Language, string>>;

export type StringKey = keyof typeof STRINGS;

export function t(key: StringKey, language: Language = DEFAULT_LANGUAGE): string {
  return STRINGS[key][language];
}
