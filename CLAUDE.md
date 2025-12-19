# CLAUDE.md - AI Assistant Guide for Tripplanner

## Project Overview

**Tripplanner** is an automated flight price monitoring system designed to find cheap flights from Atlanta (ATL) to Spain during spring break (March 2025). The system continuously monitors flight prices, tracks historical data, and sends instant alerts when deals are found.

**Key Use Case**: Finding the cheapest flights to Europe (preferably Madrid, Spain area) for spring break travel within a $500-600 budget.

---

## Repository Status

**Current State**: Fully functional flight monitoring system
- **Branch**: `claude/claude-md-mjd85od5kng236vh-3LhvY`
- **Version**: 1.0.0
- **Status**: Production-ready

---

## Codebase Structure

### Actual Directory Layout

```
Tripplanner/
├── src/                        # Source code
│   ├── config.py              # Configuration management
│   ├── database.py            # SQLite database operations
│   ├── flight_scraper.py      # Flight data collection (SerpAPI, scraping)
│   ├── flight_monitor.py      # Main monitoring orchestrator
│   ├── notifications.py       # Email/SMS alert system
│   └── scheduler.py           # Continuous monitoring scheduler
├── data/                       # Data storage
│   └── flights.db             # SQLite database (auto-created)
├── logs/                       # Application logs
│   └── flight_monitor.log     # Detailed logging
├── .env                        # Environment configuration (user creates)
├── .env.example               # Configuration template
├── .gitignore                 # Git ignore rules
├── requirements.txt           # Python dependencies
├── run.py                     # Main entry point
├── README.md                  # User documentation
├── setup_instructions.md      # Quick setup guide
└── CLAUDE.md                  # This file (AI assistant guide)
```

---

## Technology Stack

**Language**: Python 3.10+

**Core Libraries**:
- `requests` - HTTP requests for API calls
- `beautifulsoup4` - HTML parsing for web scraping
- `selenium` - Browser automation (fallback)
- `python-dotenv` - Environment variable management
- `schedule` - Task scheduling
- `sqlite3` - Built-in database (no external DB needed)

**APIs & Services**:
- SerpAPI - Google Flights data (optional, 100 free searches/month)
- Gmail SMTP - Email notifications (required)
- Twilio - SMS notifications (optional)

**Data Storage**:
- SQLite database for price history and deal tracking
- File-based logging

---

## Development Workflow

### Branch Strategy

1. **Main/Master Branch**: Production-ready code
2. **Feature Branches**: Use prefix `claude/` for AI-assisted development
   - Current working branch: `claude/claude-md-mjd85od5kng236vh-3LhvY`
3. **Always develop on designated branches** - never push directly to main

### Git Practices

#### Committing Code
- Write clear, descriptive commit messages
- Use conventional commit format:
  - `feat:` for new features
  - `fix:` for bug fixes
  - `docs:` for documentation changes
  - `refactor:` for code refactoring
  - `test:` for test additions/changes
  - `chore:` for maintenance tasks

Example:
```bash
git commit -m "feat: add trip itinerary generation component"
```

#### Pushing Changes
- Always push to the designated branch: `git push -u origin <branch-name>`
- Branch names must start with `claude/` for AI-assisted work
- Retry on network errors (up to 4 times with exponential backoff)

#### Creating Pull Requests
- Provide clear title and description
- Include summary of changes (1-3 bullet points)
- Add test plan checklist
- Reference related issues

---

## Coding Conventions

### General Principles

1. **Simplicity First**: Avoid over-engineering
   - Only implement what's requested
   - Keep solutions focused and minimal
   - Don't add unnecessary features or abstractions

2. **Security**: Always consider OWASP Top 10
   - Prevent SQL injection
   - Prevent XSS attacks
   - Validate user input
   - Sanitize data appropriately
   - Use parameterized queries
   - Implement proper authentication/authorization

3. **Read Before Modify**: Always read existing code before making changes
   - Understand current patterns
   - Match existing code style
   - Preserve architectural decisions

4. **Error Handling**:
   - Only add error handling at system boundaries
   - Validate user input and external API responses
   - Trust internal code and framework guarantees
   - Don't add defensive code for impossible scenarios

5. **Comments and Documentation**:
   - Only add comments where logic isn't self-evident
   - Don't add docstrings to unchanged code
   - Keep comments up-to-date with code changes

### File Operations

- **Prefer editing over creating**: Always modify existing files when possible
- **Delete unused code completely**: No backwards-compatibility hacks
- **No placeholder files**: Only create files that serve immediate purposes

### Code Style

*To be updated based on adopted linting rules and style guides*

---

## Testing Strategy

### Test Requirements

1. **Write tests for**:
   - New features
   - Bug fixes (regression tests)
   - Critical business logic
   - API endpoints
   - Utility functions

2. **Test organization**:
   - Co-locate tests with source files or use dedicated test directory
   - Name test files: `*.test.ts`, `*.spec.ts`, or similar
   - Group related tests using describe blocks

3. **Before committing**:
   - Run full test suite
   - Ensure all tests pass
   - Fix any failing tests before pushing

---

## Project-Specific Guidelines

### Flight Price Monitoring Domain

This is a specialized application for monitoring and alerting on flight prices. Key domain concepts:

1. **Data Models**:
   - `flight_prices` - Individual flight records with price, route, dates
   - `price_history` - Historical price tracking for trend analysis
   - `alerts_sent` - Track which deals have been notified

2. **Core Features**:
   - **Direct Flight Search**: Search multiple Spanish destinations
   - **Flexible Date Search**: Search ±N days from target dates
   - **Multi-leg Optimization**: Find cheaper routes via European hubs (e.g., ATL→London→Madrid)
   - **Price Tracking**: Store all prices, detect trends
   - **Smart Alerting**: Only alert on genuine deals, avoid duplicates
   - **Continuous Monitoring**: Run on schedule (every N hours)

3. **Search Strategy**:
   - Primary: Madrid (friend there)
   - Secondary: Barcelona, Valencia, Seville, Malaga
   - Multi-leg: Via London, Paris, Amsterdam, Frankfurt, Rome
   - Budget: $500-600 target
   - Dates: March 20-29, 2025 (flexible ±3 days)

4. **Alert Logic**:
   - Send alert if price ≤ MAX_PRICE
   - Detect "new low" prices for a route
   - Detect "significant price drops" (>$50)
   - Never send duplicate alerts for same flight
   - Include both email (required) and SMS (optional)

---

## API Integration Guidelines

### Current Integrations

1. **SerpAPI (Optional but Recommended)**
   - Service: Google Flights data via SerpAPI
   - Free tier: 100 searches/month
   - Configuration: `SERPAPI_KEY` in .env
   - Used in: `src/flight_scraper.py`
   - Fallback: Direct scraping if no API key

2. **Gmail SMTP (Required)**
   - Service: Email notifications
   - Uses Gmail App Password (NOT regular password)
   - Configuration: `EMAIL_FROM`, `EMAIL_PASSWORD` in .env
   - Used in: `src/notifications.py`
   - Security: Must use 2FA + App Password

3. **Twilio (Optional)**
   - Service: SMS notifications
   - Configuration: `TWILIO_*` variables in .env
   - Used in: `src/notifications.py`
   - Fallback: Email-only if not configured

### API Best Practices
- **Rate Limiting**: 2-second delays between searches
- **Error Handling**: Try primary API, fall back to alternatives
- **Caching**: Database stores results, no need to re-query same data
- **Security**: All API keys in .env (never commit)
- **Free Tiers**: Optimize for free tier limits (100 SerpAPI calls/month)

---

## Performance Considerations

1. **Frontend**:
   - Lazy load components and routes
   - Optimize images and assets
   - Minimize bundle size
   - Implement proper caching strategies

2. **Backend**:
   - Optimize database queries
   - Implement caching where beneficial
   - Use pagination for large datasets
   - Consider rate limiting

3. **Database**:
   - Add appropriate indexes
   - Optimize complex queries
   - Regular performance monitoring

---

## Security Best Practices

### Authentication & Authorization
- Implement proper session management
- Use secure password hashing (bcrypt, Argon2)
- Implement JWT securely if used
- Add CSRF protection
- Use HTTPS in production

### Data Protection
- Validate and sanitize all user inputs
- Use parameterized queries for database operations
- Implement proper CORS policies
- Secure sensitive configuration with environment variables
- Regular security audits

### Common Vulnerabilities to Avoid
- SQL Injection
- Cross-Site Scripting (XSS)
- Cross-Site Request Forgery (CSRF)
- Command Injection
- Path Traversal
- Insecure Deserialization

---

## Deployment

*To be updated with deployment procedures*

### Environments
- Development
- Staging
- Production

### Deployment Checklist
- [ ] All tests passing
- [ ] Code reviewed
- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] Security scan completed
- [ ] Performance tested
- [ ] Documentation updated

---

## Common Tasks for AI Assistants

### When Adding New Features
1. Read related existing code first
2. Use TodoWrite to plan multi-step tasks
3. Follow existing patterns and conventions
4. Write tests for new functionality
5. Update relevant documentation
6. Commit with clear messages
7. Push to designated branch

### When Fixing Bugs
1. Reproduce the bug
2. Identify root cause
3. Write regression test
4. Implement fix
5. Verify test passes
6. Check for similar issues elsewhere
7. Commit and push

### When Refactoring
1. Ensure test coverage exists
2. Make incremental changes
3. Run tests after each change
4. Don't mix refactoring with feature work
5. Preserve existing behavior

### When Reviewing Code
1. Check for security vulnerabilities
2. Verify test coverage
3. Ensure code follows conventions
4. Look for edge cases
5. Validate error handling

---

## Tools and Commands

### Recommended Tools
*To be updated as tooling is established*

### Common Commands

```bash
# Development
npm start / yarn start / npm run dev

# Testing
npm test / yarn test
npm run test:coverage

# Building
npm run build / yarn build

# Linting
npm run lint / yarn lint
npm run lint:fix

# Type checking (if TypeScript)
npm run type-check / tsc --noEmit
```

---

## Troubleshooting

### Common Issues

*To be populated as common issues are identified*

### Getting Help

1. Check existing documentation
2. Search closed issues on GitHub
3. Review commit history for context
4. Ask clarifying questions before making assumptions

---

## Contributing

### For AI Assistants
1. Always work on designated branches
2. Use TodoWrite for task planning
3. Follow the coding conventions above
4. Prioritize security and simplicity
5. Test thoroughly before committing
6. Write clear commit messages
7. Don't create unnecessary files

### Quality Standards
- Code must be functional and tested
- Security vulnerabilities must be addressed
- Follow established patterns
- Documentation must be updated
- No over-engineering

---

## Document Maintenance

This CLAUDE.md file should be updated whenever:
- Project structure changes significantly
- New conventions are adopted
- Technology stack is modified
- New integrations are added
- Common patterns emerge
- Important lessons are learned

**Last Updated**: 2025-12-19
**Last Updated By**: Claude (Production release)
**Current Branch**: `claude/claude-md-mjd85od5kng236vh-3LhvY`
**Version**: 1.0.0 - Fully functional flight monitoring system

---

## Quick Reference for AI Assistants

### Before Starting Work
- [ ] Read this CLAUDE.md file
- [ ] Understand the current task
- [ ] Check which branch to work on
- [ ] Read related existing code

### During Development
- [ ] Use TodoWrite for multi-step tasks
- [ ] Follow existing patterns
- [ ] Write secure code (check OWASP Top 10)
- [ ] Keep changes minimal and focused
- [ ] Write/update tests

### Before Committing
- [ ] Run tests (all must pass)
- [ ] Review changes for security issues
- [ ] Ensure code follows conventions
- [ ] Write clear commit message
- [ ] Update documentation if needed

### After Development
- [ ] Push to designated branch
- [ ] Update CLAUDE.md if patterns changed
- [ ] Create PR with clear description
- [ ] Verify CI/CD passes

---

## Notes

This document is a living guide that grows with the project. As the Tripplanner codebase develops, this file should be continuously updated to reflect current practices, conventions, and architectural decisions.

For questions or clarifications, reference this document first, then ask specific questions about unclear aspects.
