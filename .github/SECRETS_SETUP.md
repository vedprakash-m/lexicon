# GitHub Secrets Setup Guide

This guide explains how to configure the required secrets for the CI/CD pipeline.

## Required Secrets for Full CI/CD Functionality

### Vercel Deployment (Optional)

To enable Vercel deployment, configure these secrets in your GitHub repository:

1. **VERCEL_TOKEN**: Your Vercel authentication token
   - Go to [Vercel Dashboard](https://vercel.com/account/tokens)
   - Create a new token
   - Copy the token value

2. **VERCEL_ORG_ID**: Your Vercel organization ID
   - Found in your Vercel project settings
   - Or run `npx vercel env ls` in your project

3. **VERCEL_PROJECT_ID**: Your Vercel project ID
   - Found in your Vercel project settings
   - Or in the `.vercel/project.json` file after linking

### How to Add Secrets

1. Go to your GitHub repository
2. Navigate to Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Add each secret with the exact name and value

## Current CI/CD Status

- ✅ **Quality Checks**: Always run (tests, linting, type checking)
- ✅ **Desktop Builds**: Always run (macOS, Windows, Linux)
- ✅ **Security Audits**: Always run
- ✅ **Storybook Deployment**: Always run (deploys to GitHub Pages)
- ⚠️ **Vercel Deployment**: Runs but will fail gracefully if secrets are missing

## Notes

- The CI/CD pipeline will continue to work without Vercel secrets
- Vercel deployment will show as failed but won't break the entire pipeline
- All other deployments and builds will continue normally
