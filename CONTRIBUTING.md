# Contributing to Cost Melt

Thank you for your interest in contributing to Cost Melt! This document provides guidelines and instructions for contributing.

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on what is best for the community

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/dmeltonyan/costmelt/issues)
2. If not, create a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Python/Node versions, etc.)
   - Error messages or logs

### Suggesting Features

1. Check if the feature has already been suggested
2. Open an issue with:
   - Clear description of the feature
   - Use case and benefits
   - Potential implementation approach (if you have ideas)

### Submitting Pull Requests

1. **Fork the repository**
2. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes:**
   - Follow coding style guidelines
   - Add tests for new features
   - Update documentation as needed
4. **Test your changes:**
   ```bash
   # Backend tests
   cd backend
   pytest
   
   # Frontend tests
   cd ../dashboard
   npm test
   ```
5. **Commit with clear messages:**
   ```bash
   git commit -m "feat: add new feature"
   git commit -m "fix: resolve bug"
   ```
6. **Push and open a PR:**
   - Provide clear description
   - Reference related issues
   - Include screenshots if UI changes

## Coding Standards

### Python
- Follow PEP 8
- Use type hints
- Include docstrings
- Maximum line length: 100 characters

### TypeScript/React
- Follow Next.js conventions
- Use TypeScript strictly
- Format with Prettier
- Use functional components with hooks

### Commit Messages
Use [Conventional Commits](https://www.conventionalcommits.org/):
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes
- `refactor:` Code refactoring
- `test:` Adding tests
- `chore:` Maintenance tasks

## Development Setup

See [SETUP.md](./SETUP.md) for detailed setup instructions.

## Questions?

Open an issue or reach out to the maintainers.

Thank you for contributing! 🎉

