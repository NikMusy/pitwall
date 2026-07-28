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
  thisMachine: { ru: 'эта машина', en: 'this machine' },
  driverAddress: { ru: 'Адрес пилота', en: 'Driver address' },
  driverAddressHint: {
    ru: 'пусто — своя машина, иначе host:порт',
    en: 'blank for this machine, else host:port',
  },
  roomCode: { ru: 'Код комнаты', en: 'Room code' },
  tokenOptional: { ru: 'Токен (если задан)', en: 'Token (if set)' },
  join: { ru: 'Подключиться', en: 'Connect' },
  disconnect: { ru: 'Отключиться', en: 'Disconnect' },
  speed: { ru: 'Скорость', en: 'Speed' },
  rpm: { ru: 'Обороты', en: 'RPM' },
  gear: { ru: 'Передача', en: 'Gear' },
  throttle: { ru: 'Газ', en: 'Throttle' },
  brake: { ru: 'Тормоз', en: 'Brake' },
  fuel: { ru: 'Топливо', en: 'Fuel' },
  lap: { ru: 'Круг', en: 'Lap' },
  lapTime: { ru: 'Время круга', en: 'Lap time' },
  tyreFl: { ru: 'Шина FL', en: 'Tyre FL' },
  tyreFr: { ru: 'Шина FR', en: 'Tyre FR' },
  tyreRl: { ru: 'Шина RL', en: 'Tyre RL' },
  tyreRr: { ru: 'Шина RR', en: 'Tyre RR' },
} as const satisfies Record<string, Record<Language, string>>;

export type StringKey = keyof typeof STRINGS;

export function t(key: StringKey, language: Language = DEFAULT_LANGUAGE): string {
  return STRINGS[key][language];
}
