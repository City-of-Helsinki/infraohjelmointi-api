export default {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'header-max-length': [2, 'always', 150],
    'type-empty': [1, 'never'],
    'subject-empty': [1, 'never'],
  },
};
