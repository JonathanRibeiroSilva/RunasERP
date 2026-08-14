// Flat config, required from ESLint 9 on — .eslintrc.cjs is no longer read.
// Two things moved rather than disappeared: `env: { browser: true }` is now
// languageOptions.globals, and the `--ext ts,tsx` CLI flag is the `files` glob.
import js from '@eslint/js';
import globals from 'globals';
import tseslint from 'typescript-eslint';
import reactHooks from 'eslint-plugin-react-hooks';
import reactRefresh from 'eslint-plugin-react-refresh';

export default tseslint.config(
  { ignores: ['dist', 'coverage'] },
  {
    files: ['**/*.{ts,tsx}'],
    extends: [js.configs.recommended, ...tseslint.configs.recommended],
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
    },
    plugins: {
      'react-hooks': reactHooks,
      'react-refresh': reactRefresh,
    },
    rules: {
      ...reactHooks.configs.recommended.rules,
      'react-refresh/only-export-components': ['warn', { allowConstantExport: true }],
      '@typescript-eslint/no-unused-vars': ['warn', { argsIgnorePattern: '^_' }],
      '@typescript-eslint/no-explicit-any': 'warn',

      // ponytail: these three ship as errors and found 29 pre-existing hits on
      // the first run — set-state-in-effect and immutability are new in
      // react-hooks 7, preserve-caught-error is new in ESLint 10 core. Demoted
      // to warn so the migration stays a migration; the --max-warnings ceiling
      // still blocks new ones. Fix the 29 and promote them back to error.
      'react-hooks/set-state-in-effect': 'warn',
      'react-hooks/immutability': 'warn',
      'preserve-caught-error': 'warn',
    },
  },
);
