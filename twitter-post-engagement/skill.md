---
name: openclaw-twitter-oauth
description: "Publish posts to X/Twitter through an OAuth-based authorization flow. If posting requires authorization, return an approval link so the user can grant access and continue posting."
homepage: https://openclaw.ai
metadata: {"openclaw":{"emoji":"","requires":{"bins":["python3"],"env":["AISA_API_KEY"]},"primaryEnv":"AISA_API_KEY"}}
---

# OpenClaw Twitter OAuth

**OAuth-based X/Twitter posting for autonomous agents. Powered by AIsa.**

One API key. Simple authorization. Direct posting.

## What Can You Do?

### Publish Posts
```text
Help me post this to Twitter: Today we released a new version.
```

### Return Authorization Links When Needed
```text
Post this to X, and if authorization is needed, give me the approval link.
```

### Continue After Approval
```text
I already authorized Twitter. Post this update now.
```

## Quick Start

```bash
export AISA_API_KEY="your-key"
```

## Python Client

```bash
# Show current client configuration
python3 {baseDir}/scripts/twitter_oauth_client.py status

# Request an authorization link
python3 {baseDir}/scripts/twitter_oauth_client.py authorize

# Request an authorization link and open it in the browser
python3 {baseDir}/scripts/twitter_oauth_client.py authorize --open-browser

# Publish a post
python3 {baseDir}/scripts/twitter_oauth_client.py post --text "Hello from Twitter OAuth"

# Reply to a specific tweet
python3 {baseDir}/scripts/twitter_oauth_client.py post --text "Reply content" --in-reply-to-tweet-id "1888888888888888888"

```

## Core Behavior

This skill is designed around the user intent of posting to X/Twitter.

Recommended flow:

1. Try to publish the requested content first.
2. If posting fails because access has not been authorized yet, return an authorization link.
3. After the user completes authorization, publish using the authorized account.

## Commands

### `status`

Show the current local client configuration.

### `authorize`

Request an authorization link for the current user context.

### `post`

Publish a post. If content exceeds 280 characters, the client automatically splits it and publishes a chained thread where each follow-up tweet replies to the previous tweet using `in_reply_to_tweet_id`.

If the current user is not authorized yet, the caller should guide the user through authorization and retry posting afterward.

## Agent Instructions

When the user asks to publish content to X/Twitter:

1. Check whether `AISA_API_KEY` is configured.
2. Try `post` first when the user intent is to publish content.
3. If posting indicates that authorization is required, run `authorize` and return the approval link.
4. Do not claim the post succeeded until the publish step actually succeeds.

## Guardrails

- Do not ask the user for their Twitter password.
- Do not use cookie-based login or proxy-based login unless the user explicitly asks for legacy behavior.
- Do not claim authorization succeeded just because an authorization URL was generated.
