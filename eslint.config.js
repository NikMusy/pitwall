import js from '@eslint/js';
import tseslint from 'typescript-eslint';

export default tseslint.config(
  {
    ignores: [
      '**/dist/**',
      '**/node_modules/**',
      'packages/schema/generated/**',
      // Python virtualenv: pywebview ships browser-side JS that is not ours.
      '.venv/**',
      'packaging/build/**',
    ],
  },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    files: ['**/*.{ts,tsx}'],
    rules: {
      '@typescript-eslint/consistent-type-imports': 'error',
      // Telemetry buffers are typed arrays and unions of raw numbers; `any`
      // hides exactly the mistakes that matter here.
      '@typescript-eslint/no-explicit-any': 'error',
    },
  },
);
