# Contributing to Agentic Calendar Spread Trading System

Thank you for your interest in contributing to this project! This document provides guidelines for contributing.

## Development Setup

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/yourusername/agentic-calendar-trading.git
   cd agentic-calendar-trading
   ```
3. Create a virtual environment and install dependencies:
   ```bash
   ./run.sh
   ```

## How to Contribute

### Reporting Issues

- Use the GitHub Issues tab to report bugs
- Include detailed information about the issue
- Provide steps to reproduce the problem
- Include system information (OS, Python version, etc.)

### Feature Requests

- Open an issue with the "enhancement" label
- Describe the feature and its use case
- Discuss the implementation approach

### Code Contributions

1. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes following these guidelines:
   - Follow PEP 8 for Python code
   - Use meaningful variable and function names
   - Add comments for complex logic
   - Update documentation as needed

3. Test your changes:
   ```bash
   python -m pytest tests/  # when tests are added
   ```

4. Commit your changes:
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

5. Push and create a pull request:
   ```bash
   git push origin feature/your-feature-name
   ```

## Code Style

- Python: Follow PEP 8
- JavaScript: Use ES6+ features, consistent indentation
- CSS: Use BEM methodology where applicable
- HTML: Semantic markup, proper indentation

## Project Structure

- `app.py` - Main Flask application
- `static/` - Frontend assets (CSS, JS, images, data)
- `templates/` - HTML templates
- `requirements.txt` - Python dependencies

## Areas for Contribution

- Real market data integration (Alpha Vantage, Polygon, etc.)
- Database integration (SQLAlchemy)
- User authentication and portfolios
- Advanced trading strategies
- Mobile responsive improvements
- Unit and integration tests
- Documentation improvements

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.
