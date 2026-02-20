# LinkedIn App Setup for Auto Post Skill

This document provides instructions for setting up a LinkedIn application to use the auto post skill.

## Prerequisites

- LinkedIn account (personal or business)
- Admin access to a LinkedIn company page (optional, if posting on behalf of a company)
- Valid business email associated with LinkedIn account

## Step 1: Create a LinkedIn App

1. Go to the [LinkedIn Developer Portal](https://www.linkedin.com/developers/)
2. Sign in with your LinkedIn credentials
3. Click on "Create App" in the top right corner
4. Fill in the application details:
   - **App Name**: Your application name (e.g., "AI Employee Auto Poster")
   - **App Description**: Description of your application
   - **App Logo**: Upload a logo (optional)
   - **Website URL**: Your company website or a placeholder URL
   - **Authorized Redirect URLs**: Add your redirect URLs (e.g., `http://localhost:8000/callback`)
5. Accept the terms and conditions
6. Click "Create Application"

## Step 2: Configure App Settings

After creating your app, you'll land on the app's credentials page. Note down:

- **Client ID**: Needed for authentication
- **Client Secret**: Needed for authentication (keep this secure)
- **OAuth 2.0 Settings**: Configure your OAuth 2.0 settings

## Step 3: Request App Verification (if needed)

For production use, your app will need to be verified by LinkedIn:

1. Go to the "Products" tab in your app dashboard
2. For UGC Post API access, you'll need to apply for verification
3. Prepare documentation about how you'll use the APIs
4. Submit for review

## Step 4: Enable Required Products

Make sure to enable these products in your app dashboard:

### UGC Posts API (for posting)
This API allows the creation of native posts on LinkedIn.

**Permissions required**:
- `w_member_social` - Allows writing posts on behalf of a member
- `w_organization_social` (optional) - Allows writing posts on behalf of an organization

### Sign In with LinkedIn (for authentication)
**Permissions required**:
- `r_liteprofile` - Basic profile information
- `r_emailaddress` - Email address
- `w_member_social` - For posting

## Step 5: OAuth 2.0 Authentication Flow

The LinkedIn auto post skill will use the OAuth 2.0 authorization code flow:

### Step 1: Authorization Request
Redirect the user to LinkedIn's authorization URL:
```
https://www.linkedin.com/oauth/v2/authorization?
    response_type=code&
    client_id=YOUR_CLIENT_ID&
    redirect_uri=YOUR_REDIRECT_URI&
    scope=w_member_social
```

### Step 2: Token Exchange
Exchange the authorization code for an access token:
```
POST https://www.linkedin.com/oauth/v2/accessToken
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code&
code=AUTHORIZATION_CODE&
redirect_uri=YOUR_REDIRECT_URI&
client_id=YOUR_CLIENT_ID&
client_secret=YOUR_CLIENT_SECRET
```

## Step 6: Access Token Usage

Once you have the access token, you can make API calls:

### For posting to personal profile:
- Scope needed: `w_member_social`
- API: UGC Posts API

### For posting to company page:
- Scope needed: `w_organization_social`
- Additional step: Get organization URN

## Step 7: Getting Organization URN (for company page posts)

If you want to post on behalf of a company:

1. Get your organization URNs:
```
GET https://api.linkedin.com/v2/organizations?oauth2_access_token=YOUR_ACCESS_TOKEN
```

2. Use the organization URN in the post payload instead of personal URN

## Step 8: Environment Configuration

Create a `.env` file in your project root:

```env
LINKEDIN_CLIENT_ID=your_client_id_here
LINKEDIN_CLIENT_SECRET=your_client_secret_here
LINKEDIN_REDIRECT_URI=http://localhost:8000/callback
LINKEDIN_ACCESS_TOKEN=your_access_token_here  # This will be generated through OAuth flow
```

## Step 9: Required Scopes Summary

For the LinkedIn auto post skill, you need these scopes:

- **w_member_social**: Required for posting to personal LinkedIn profile
  - Allows creating posts on behalf of the user
  - Allows commenting and liking posts

- **w_organization_social**: Optional, for posting to company pages
  - Allows creating posts on behalf of an organization
  - Requires additional organization permissions

## API Rate Limits

LinkedIn has rate limits that you should be aware of:

- **Per-application per-second**: Limited number of calls per second
- **Per-application per-minute**: Higher limit per minute
- **Per-application per-day**: Daily limit

The auto-post skill includes 5-minute intervals between checks to help stay within limits.

## Error Handling

Common LinkedIn API errors you might encounter:

- `401 Unauthorized`: Invalid or expired access token
- `403 Forbidden`: Insufficient permissions
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: LinkedIn-side issue

## Testing Your Setup

1. After setting up the app and getting your credentials, you can test the connection:
```python
import requests

headers = {
    'Authorization': 'Bearer YOUR_ACCESS_TOKEN'
}

# Test basic profile access
response = requests.get('https://api.linkedin.com/v2/me', headers=headers)
print(response.json())
```

2. To test post creation, you can use the auto-post skill after configuring credentials.

## Security Best Practices

- Store access tokens securely (preferably encrypted)
- Use refresh tokens to maintain long-term access
- Implement proper token expiration handling
- Never commit credentials to version control
- Use environment variables for configuration
- Implement proper error logging without exposing sensitive information

## Troubleshooting

### Common Issues:

1. **"Not enough permissions" error**:
   - Ensure your app has been granted the required permissions
   - Check that the access token includes the necessary scopes

2. **"Invalid redirect URI" error**:
   - Make sure the redirect URI matches exactly what's configured in your LinkedIn app
   - Include the exact protocol (http/https)

3. **App not showing in LinkedIn account**:
   - Apps are tied to the LinkedIn account they were created with
   - Make sure you're logging in with the same account

4. **API access denied**:
   - For production use, your app may need LinkedIn verification
   - Check if your use case requires special permissions