# Demo Package

**DEMO ONLY – NOT FOR PRODUCTION**

## Purpose

This demo package is designed for project review demonstrations. It provides simulated functionality to showcase the system's capabilities without affecting production or research pipelines.

## What is Simulated

- **Mock Data**: Demo routes use simulated/mock data instead of real database queries
- **Simulated Responses**: API responses are generated for demonstration purposes
- **No Real Transactions**: No actual financial transactions or data modifications occur
- **No ML Training**: Machine learning models are not trained or updated during demos
- **No Database Writes**: Demo functionality does not write to production databases

## What is NOT Real

- **No Real User Data**: Demo does not access or modify real user accounts
- **No Real Transactions**: Financial transactions shown are simulated
- **No Real Listings**: Product listings displayed are mock data
- **No Real ML Predictions**: Any ML model outputs are simulated
- **No Real Database Operations**: All database operations are mocked

## Activation

Demo functionality is only available when `DEMO_MODE=True` is set in the environment configuration.

**Default**: `DEMO_MODE=False` (disabled by default)

**To enable for demos**: Set `DEMO_MODE=true` in your `.env` file or environment variables.

## Security & Isolation

- Demo routes are completely isolated from production routes
- Demo code does not modify core application logic
- Demo functionality cannot access production data
- Clear separation ensures no impact on production or research pipelines

## Usage

Demo routes will only be registered and accessible when:
1. `DEMO_MODE=True` is set in configuration
2. Routes are explicitly added to the demo package
3. Routes include proper demo-only guards

## Important Notes

⚠️ **This functionality is for demonstration purposes only**

- Never enable `DEMO_MODE` in production environments
- Never use demo routes for actual user operations
- Demo code should be clearly marked with "DEMO ONLY" comments
- All demo routes must check `DEMO_MODE` before execution

