# OpenClaw Twitter 🐦

Twitter/X read APIs and **OAuth-based posting** for autonomous agents. Powered by AIsa.

## Installation

```bash
export AISA_API_KEY="your-key"
```

## Quick Start

```bash
# Read: user + search
python scripts/twitter_client.py user-info --username elonmusk
python scripts/twitter_client.py search --query "AI agents"
python scripts/twitter_client.py trends

# Post: OAuth relay
python scripts/twitter_client.py authorize --open-browser
python scripts/twitter_client.py post --text "Hello"
```

## Features

- **Read**: User info, tweets, search, trends, followers, lists, communities, Spaces, etc.
- **Post**: Browser OAuth via `POST /twitter/auth_twitter` and `POST /twitter/post_twitter` with `aisa_api_key` in the JSON body (no cookies, no proxy, no password).


## Get API Key

Sign up at [aisa.one](https://aisa.one)

## Links

- [ClawHub](https://www.clawhub.com/aisa-one/openclaw-twitter)
- [API Reference](https://docs.aisa.one/reference/)
