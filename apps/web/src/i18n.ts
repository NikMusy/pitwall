// Minimal typed dictionary. A real i18n library earns its place when we have
// plurals and interpolation to worry about; right now it would be weight
// without benefit.

export const LANGUAGES = ['ru', 'en'] as const;
export type Language = (typeof LANGUAGES)[number];

export const DEFAULT_LANGUAGE: Language = 'ru';

const STRINGS = {
  appName: { ru: 'PitWall', en: 'PitWall' },
  noAgent: { ru: 'Телеметрии нет', en: 'No telemetry' },
  live: { ru: 'Данные идут', en: 'Live' },
  notJoined: { ru: 'не подключено', en: 'not joined' },
  roomCode: { ru: 'Код комнаты', en: 'Room code' },
  tokenOptional: { ru: 'Токен (если задан)', en: 'Token (if set)' },
  join: { ru: 'Подключиться', en: 'Join' },
  speed: { ru: 'Скорость', en: 'Speed' },
  rpm: { ru: 'Обороты', en: 'RPM' },
  gear: { ru: 'Передача', en: 'Gear' },
  throttle: { ru: 'Газ', en: 'Throttle' },
  brake: { ru: 'Тормоз', en: 'Brake' },
  fuel: { ru: 'Топливо', en: 'Fuel' },
  lap: { ru: 'Круг', en: 'Lap' },
  lapTime: { ru: 'Время круга', en: 'Lap time' },
} as const satisfies Record<string, Record<Language, string>>;

export type StringKey = keyof typeof STRINGS;

export function t(key: StringKey, language: Language = DEFAULT_LANGUAGE): string {
  return STRINGS[key][language];
}
