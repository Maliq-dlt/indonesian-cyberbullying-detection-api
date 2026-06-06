## Pull Request Checklist

### Description
Provide a concise summary of the changes introduced by this PR. Mention any related issues using `Fixes #` or `Closes #`.

### Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Refactoring / Code Quality (no logic changes)
- [ ] Documentation update

### How Has This Been Tested?
Please describe the tests that you ran to verify your changes. Provide instructions so we can reproduce.
1. Run backend tests: `pytest cyberbullying_api/tests`
2. Run frontend build: `npm run build`
3. Manual verification step [...]

### Checklist:
- [ ] My code follows the style guidelines of this project
- [ ] My changes generate no new linting errors or warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] Any dependent changes have been merged and published in downstream modules
- [ ] I have updated the documentation (`README.md`, inline comments, etc.) accordingly
- [ ] I have verified that no sensitive credentials, keys, or cookies are added to the codebase
