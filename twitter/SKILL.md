---
name: Twitter Command Center (Search + Post)
description: "Searches and reads X (Twitter): profiles, timelines, mentions, followers, tweet search, trends, lists, communities, and Spaces. Publishes posts after the user completes OAuth in the browser. Use when the user asks about Twitter/X data, social listening, or posting without sharing account passwords."
homepage: https://openclaw.ai
metadata: {"openclaw":{"emoji":"🐦","requires":{"bins":["curl","python3"],"env":["AISA_API_KEY"]},"primaryEnv":"AISA_API_KEY"}}
---

# OpenClaw Twitter 🐦

**Twitter/X data access and automation for autonomous agents. Powered by AIsa.**

One API key. Full Twitter intelligence.

## 🔥 What Can You Do?

### Monitor Influencers
```
"Get Elon Musk's latest tweets and notify me of any AI-related posts"
```

### Track Trends
```
"What's trending on Twitter worldwide right now?"
```

### Social Listening
```
"Search for tweets mentioning our product and analyze sentiment"
```

### Post After OAuth
```
"Post this to X: we shipped a new release" (authorize in browser when prompted, then post)
```

### Competitor Intel
```
"Monitor @anthropic and @GoogleAI - alert me on new announcements"
```

## Quick Start

```bash
export AISA_API_KEY="your-key"
```

## Core Capabilities

### Read Operations (No Login Required)

#### User Endpoints

```bash
# Get user info
curl "https://api.aisa.one/apis/v1/twitter/user/info?userName=elonmusk" \
  -H "Authorization: Bearer $AISA_API_KEY"

# Get user profile about (account country, verification, username changes)
curl "https://api.aisa.one/apis/v1/twitter/user_about?userName=elonmusk" \
  -H "Authorization: Bearer $AISA_API_KEY"

# Batch get user info by IDs
curl "https://api.aisa.one/apis/v1/twitter/user/batch_info_by_ids?userIds=44196397,123456" \
  -H "Authorization: Bearer $AISA_API_KEY"

# Get user's latest tweets
curl "https://api.aisa.one/apis/v1/twitter/user/last_tweets?userName=elonmusk" \
  -H "Authorization: Bearer $AISA_API_KEY"

# Get user mentions
curl "https://api.aisa.one/apis/v1/twitter/user/mentions?userName=elonmusk" \
  -H "Authorization: Bearer $AISA_API_KEY"

# Get user followers
curl "https://api.aisa.one/apis/v1/twitter/user/followers?userName=elonmusk" \
  -H "Authorization: Bearer $AISA_API_KEY"

# Get user followings
curl "https://api.aisa.one/apis/v1/twitter/user/followings?userName=elonmusk" \
  -H "Authorization: Bearer $AISA_API_KEY"

# Get user verified followers (requires user_id, not userName)
curl "https://api.aisa.one/apis/v1/twitter/user/verifiedFollowers?user_id=44196397" \
  -H "Authorization: Bearer $AISA_API_KEY"

# Check follow relationship between two users
curl "https://api.aisa.one/apis/v1/twitter/user/check_follow_relationship?source_user_name=elonmusk&target_user_name=BillGates" \
  -H "Authorization: Bearer $AISA_API_KEY"

# Search users by keyword
curl "https://api.aisa.one/apis/v1/twitter/user/search?query=AI+researcher" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

#### Tweet Endpoints

```bash
# Advanced tweet search (queryType is required: Latest or Top)
curl "https://api.aisa.one/apis/v1/twitter/tweet/advanced_search?query=AI+agents&queryType=Latest" \
  -H "Authorization: Bearer $AISA_API_KEY"

# Search top tweets
curl "https://api.aisa.one/apis/v1/twitter/tweet/advanced_search?query=AI+agents&queryType=Top" \
  -H "Authorization: Bearer $AISA_API_KEY"

# Get tweets by IDs (comma-separated)
curl "https://api.aisa.one/apis/v1/twitter/tweets?tweet_ids=1895096451033985024" \
  -H "Authorization: Bearer $AISA_API_KEY"

# Get tweet replies
curl "https://api.aisa.one/apis/v1/twitter/tweet/replies?tweetId=1895096451033985024" \
  -H "Authorization: Bearer $AISA_API_KEY"

# Get tweet quotes
curl "https://api.aisa.one/apis/v1/twitter/tweet/quotes?tweetId=1895096451033985024" \
  -H "Authorization: Bearer $AISA_API_KEY"

# Get tweet retweeters
curl "https://api.aisa.one/apis/v1/twitter/tweet/retweeters?tweetId=1895096451033985024" \
  -H "Authorization: Bearer $AISA_API_KEY"

# Get tweet thread context (full conversation thread)
curl "https://api.aisa.one/apis/v1/twitter/tweet/thread_context?tweetId=1895096451033985024" \
  -H "Authorization: Bearer $AISA_API_KEY"

# Get article by tweet ID
curl "https://api.aisa.one/apis/v1/twitter/article?tweet_id=1895096451033985024" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

#### Trends, Lists, Communities & Spaces

```bash
# Get trending topics (worldwide)
curl "https://api.aisa.one/apis/v1/twitter/trends?woeid=1" \
  -H "Authorization: Bearer $AISA_API_KEY"

# Get list members
curl "https://api.aisa.one/apis/v1/twitter/list/members?list_id=1585430245762441216" \
  -H "Authorization: Bearer $AISA_API_KEY"

# Get list followers
curl "https://api.aisa.one/apis/v1/twitter/list/followers?list_id=1585430245762441216" \
  -H "Authorization: Bearer $AISA_API_KEY"

# Get community info
curl "https://api.aisa.one/apis/v1/twitter/community/info?community_id=1708485837274263614" \
  -H "Authorization: Bearer $AISA_API_KEY"

# Get community members
curl "https://api.aisa.one/apis/v1/twitter/community/members?community_id=1708485837274263614" \
  -H "Authorization: Bearer $AISA_API_KEY"

# Get community moderators
curl "https://api.aisa.one/apis/v1/twitter/community/moderators?community_id=1708485837274263614" \
  -H "Authorization: Bearer $AISA_API_KEY"

# Get community tweets
curl "https://api.aisa.one/apis/v1/twitter/community/tweets?community_id=1708485837274263614" \
  -H "Authorization: Bearer $AISA_API_KEY"

# Search tweets from all communities
curl "https://api.aisa.one/apis/v1/twitter/community/get_tweets_from_all_community?query=AI" \
  -H "Authorization: Bearer $AISA_API_KEY"

# Get Space detail
curl "https://api.aisa.one/apis/v1/twitter/spaces/detail?space_id=1dRJZlbLkjexB" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

### Posting (OAuth relay)

Posting does **not** use cookies, passwords, or proxies. Use the AIsa OAuth relay endpoints:

- `POST /apis/v1/twitter/auth_twitter` — returns an authorization URL for the user to open in a browser
- `POST /apis/v1/twitter/post_twitter` — publishes content after the user has authorized

Both relay requests send **`aisa_api_key` in the JSON body**. Do **not** rely on `Authorization: Bearer` for these two POSTs.

Required / optional JSON body fields:

- `auth_twitter`: `aisa_api_key` (required)
- `post_twitter`: `aisa_api_key` (required), `content` (required), `media_ids` (optional array), `type` (optional string: `quote` or `reply`), `quote_tweet_id` (optional string, internal chaining support)

```bash
# Request authorization URL
curl -X POST "https://api.aisa.one/apis/v1/twitter/auth_twitter" \
  -H "Content-Type: application/json" \
  -d "{\"aisa_api_key\":\"$AISA_API_KEY\"}"

# Publish a post (after user completes OAuth in browser)
curl -X POST "https://api.aisa.one/apis/v1/twitter/post_twitter" \
  -H "Content-Type: application/json" \
  -d "{\"aisa_api_key\":\"$AISA_API_KEY\",\"content\":\"Hello from OpenClaw!\",\"type\":\"quote\"}"
```

## Agent Instructions (posting)

When the user asks to publish to X/Twitter:

1. Ensure `AISA_API_KEY` is set.
2. Prefer `post` when the user wants to publish; if the API indicates authorization is required, run `authorize` and return the `authorization_url` (or `data.auth_url` from the raw response).
3. Default to `--type quote` for publishing. Only pass `--type reply` when the user explicitly says they want to reply.
4. In this skill, `reply` only controls the `type` argument passed to the Python client. It does not require asking the user for a target tweet URL or tweet ID.
5. If the user says things like `use reply mode to post: ...`, `使用reply方式发送推文：...`, or `reply发这条：...`, run the `post` command directly with `--type reply`.
6. Do not ask follow-up questions about which tweet to reply to unless the user explicitly asks to target a specific tweet.
7. Do not ask for Twitter passwords or use cookie/proxy login flows.
8. Do not claim the post succeeded until `post` returns success.

#### Character Limit & Thread Splitting Rules:
1. Maximum 280 characters per tweet (Chinese/full-width characters/Emojis count as 1 character each);
2. If content exceeds 280 characters:
   - The Python client automatically splits content into chunks before publishing;
   - Follow-up chunks are published as a chained thread by quoting the previous tweet with `quote_tweet_id`;
3. If any chunk fails to post, the entire thread publishing stops and returns an error.

## Python Client

```bash
# User operations
python3 {baseDir}/scripts/twitter_client.py user-info --username elonmusk
python3 {baseDir}/scripts/twitter_client.py user-about --username elonmusk
python3 {baseDir}/scripts/twitter_client.py tweets --username elonmusk
python3 {baseDir}/scripts/twitter_client.py mentions --username elonmusk
python3 {baseDir}/scripts/twitter_client.py followers --username elonmusk
python3 {baseDir}/scripts/twitter_client.py followings --username elonmusk
python3 {baseDir}/scripts/twitter_client.py verified-followers --user-id 44196397
python3 {baseDir}/scripts/twitter_client.py check-follow --source elonmusk --target BillGates

# Search & Discovery
python3 {baseDir}/scripts/twitter_client.py search --query "AI agents"
python3 {baseDir}/scripts/twitter_client.py search --query "AI agents" --type Top
python3 {baseDir}/scripts/twitter_client.py user-search --query "AI researcher"
python3 {baseDir}/scripts/twitter_client.py trends --woeid 1

# Tweet operations
python3 {baseDir}/scripts/twitter_client.py detail --tweet-ids 1895096451033985024
python3 {baseDir}/scripts/twitter_client.py replies --tweet-id 1895096451033985024
python3 {baseDir}/scripts/twitter_client.py quotes --tweet-id 1895096451033985024
python3 {baseDir}/scripts/twitter_client.py retweeters --tweet-id 1895096451033985024
python3 {baseDir}/scripts/twitter_client.py thread --tweet-id 1895096451033985024

# List operations
python3 {baseDir}/scripts/twitter_client.py list-members --list-id 1585430245762441216
python3 {baseDir}/scripts/twitter_client.py list-followers --list-id 1585430245762441216

# Community operations
python3 {baseDir}/scripts/twitter_client.py community-info --community-id 1708485837274263614
python3 {baseDir}/scripts/twitter_client.py community-members --community-id 1708485837274263614
python3 {baseDir}/scripts/twitter_client.py community-tweets --community-id 1708485837274263614
python3 {baseDir}/scripts/twitter_client.py community-search --query "AI"

# OAuth posting
python3 {baseDir}/scripts/twitter_client.py status
python3 {baseDir}/scripts/twitter_client.py authorize
python3 {baseDir}/scripts/twitter_client.py authorize --open-browser
python3 {baseDir}/scripts/twitter_client.py post --text "Hello from OAuth"
python3 {baseDir}/scripts/twitter_client.py post --text "Hello from OAuth" --type reply
```

## API Endpoints Reference

### Read Endpoints (GET)

| Endpoint | Description | Key Params |
|----------|-------------|------------|
| `/twitter/user/info` | Get user profile | `userName` |
| `/twitter/user_about` | Get user profile about | `userName` |
| `/twitter/user/batch_info_by_ids` | Batch get users by IDs | `userIds` |
| `/twitter/user/last_tweets` | Get user's recent tweets | `userName`, `cursor` |
| `/twitter/user/mentions` | Get user mentions | `userName`, `cursor` |
| `/twitter/user/followers` | Get user followers | `userName`, `cursor` |
| `/twitter/user/followings` | Get user followings | `userName`, `cursor` |
| `/twitter/user/verifiedFollowers` | Get verified followers | `user_id`, `cursor` |
| `/twitter/user/check_follow_relationship` | Check follow relationship | `source_user_name`, `target_user_name` |
| `/twitter/user/search` | Search users by keyword | `query`, `cursor` |
| `/twitter/tweet/advanced_search` | Advanced tweet search | `query`, `queryType` (Latest/Top), `cursor` |
| `/twitter/tweets` | Get tweets by IDs | `tweet_ids` (comma-separated) |
| `/twitter/tweet/replies` | Get tweet replies | `tweetId`, `cursor` |
| `/twitter/tweet/quotes` | Get tweet quotes | `tweetId`, `cursor` |
| `/twitter/tweet/retweeters` | Get tweet retweeters | `tweetId`, `cursor` |
| `/twitter/tweet/thread_context` | Get tweet thread context | `tweetId`, `cursor` |
| `/twitter/article` | Get article by tweet | `tweet_id` |
| `/twitter/trends` | Get trending topics | `woeid` (1=worldwide) |
| `/twitter/list/members` | Get list members | `list_id`, `cursor` |
| `/twitter/list/followers` | Get list followers | `list_id`, `cursor` |
| `/twitter/community/info` | Get community info | `community_id` |
| `/twitter/community/members` | Get community members | `community_id`, `cursor` |
| `/twitter/community/moderators` | Get community moderators | `community_id`, `cursor` |
| `/twitter/community/tweets` | Get community tweets | `community_id`, `cursor` |
| `/twitter/community/get_tweets_from_all_community` | Search all community tweets | `query`, `cursor` |
| `/twitter/spaces/detail` | Get Space detail | `space_id` |

### Post Endpoints (OAuth relay, POST)

| Endpoint | Description | Key Params |
|----------|-------------|------------|
| `/twitter/auth_twitter` | Get OAuth authorization URL | `aisa_api_key` |
| `/twitter/post_twitter` | Publish a post | `aisa_api_key`, `content`, `media_ids` (optional), `type` (optional), `quote_tweet_id` (optional, internal chaining support) |

Auth (relay only): JSON body field `aisa_api_key` (no `Authorization: Bearer` on these POSTs).

## Pricing

| API | Cost |
|-----|------|
| Twitter read query | ~$0.0004 |
| Twitter OAuth post (relay) | See [AIsa pricing](https://aisa.one) / console |

Every response includes `usage.cost` and `usage.credits_remaining`.

## Get Started

1. Sign up at [aisa.one](https://aisa.one)
2. Get your API key
3. Add credits (pay-as-you-go)
4. Set environment variable: `export AISA_API_KEY="your-key"`

## Full API Reference

See [API Reference](https://docs.aisa.one/reference/) for complete endpoint documentation.
