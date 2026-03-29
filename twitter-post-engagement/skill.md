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

### Publish Image / Video Posts
```text
Post this image to X with the caption: Shipping day.
```

```text
Post this video to Twitter.
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

# Publish a text post
python3 {baseDir}/scripts/twitter_oauth_client.py post --text "Hello from Twitter OAuth"

# Publish an image-only post
python3 {baseDir}/scripts/twitter_oauth_client.py post --media-file ./workspace/photo.png

# Publish a video-only post
python3 {baseDir}/scripts/twitter_oauth_client.py post --media-file ./workspace/demo.mp4

# Publish an image with text
python3 {baseDir}/scripts/twitter_oauth_client.py post --text "Shipping day." --media-file ./workspace/photo.png

# Publish a video with text
python3 {baseDir}/scripts/twitter_oauth_client.py post --text "Demo clip" --media-file ./workspace/demo.mp4

# Publish a threaded post using reply relationships between chunks
python3 {baseDir}/scripts/twitter_oauth_client.py post --text "Hello from Twitter OAuth" --type reply

# Start the thread from a specific external tweet
python3 {baseDir}/scripts/twitter_oauth_client.py post --text "Reply content" --in-reply-to-tweet-id "1888888888888888888"
```

## Core Behavior

This skill is designed around the user intent of posting to X/Twitter.

Recommended flow:

1. Try to publish the requested content first.
2. If posting fails because access has not been authorized yet, return an authorization link.
3. After the user completes authorization, publish using the authorized account.

### OpenClaw Attachment Flow

When the user drops image/video files into OpenClaw:

1. OpenClaw stores the attachment in the local workspace and provides the workspace file path to the skill.
2. The skill passes that local path through `--media-file <workspace_path>`.
3. The Python client reads the local file and sends it to the relay backend as `multipart/form-data`.
4. The relay backend uploads the media to Twitter/X and then publishes the tweet.
5. The skill returns the final publish result, including the tweet link or tweet ID when available.
6. If the user provides only one image, publish with only that single image. Do not duplicate it, infer extra images, or expand it into a multi-image post.
7. If the user provides media without any text, send a media-only post request. Do not synthesize, inject, or infer caption text.
8. For a normal single post with no threading context, do not send thread/relationship fields such as `type`.

## Commands

### `status`

Show the current local client configuration.

### `authorize`

Request an authorization link for the current user context.

### `post`

Publish a post.

#### Character Limit & Thread Splitting Rules:
1. Maximum 280 characters per tweet (Chinese/full-width characters/Emojis count as 1 character each);
2. If content exceeds 280 characters:
   - The Python client automatically splits content into chunks before publishing;
3. If any chunk fails to post, the multi-chunk publishing process stops and returns an error.
4. Media files are attached only to the first chunk of a multi-chunk post.

## Agent Instructions

When the user asks to publish content to X/Twitter:

1. Check whether `AISA_API_KEY` is configured.
2. Try `post` first when the user intent is to publish content.
3. If the user attached workspace files, pass each image/video path with `--media-file`.
4. If the user provided only one image attachment, pass only that one image once.
5. Support these combinations directly:
   - image only
   - video only
   - image + text
   - video + text
6. Default to `--type quote` for publishing. Only pass `--type reply` when the user explicitly says they want to use reply relationships for a threaded post.
7. In this skill, `--type reply` does not mean replying to a target tweet. It only controls how multi-chunk content is threaded.
8. If the user says things like `use reply mode to post: ...`, `post this in reply mode: ...`, or `reply-post this: ...`, run the `post` command directly with `--type reply`.
9. If the user explicitly provides a target tweet ID, include `--in-reply-to-tweet-id <tweet_id>` to start the thread from that external tweet.
10. Do not ask for a tweet link or tweet ID just because the user requested `reply`; only use `--in-reply-to-tweet-id` when the user explicitly wants to target a specific tweet.
11. If posting indicates that authorization is required, run `authorize` and return the approval link.
12. Do not claim the post succeeded until the publish step actually succeeds.

## Guardrails

- Do not ask the user for their Twitter password.
- Do not use cookie-based login or proxy-based login unless the user explicitly asks for legacy behavior.
- Do not claim authorization succeeded just because an authorization URL was generated.
- Do not ask for a tweet link or tweet ID just because the user requested `reply`; use `--type reply` directly.
- If the user explicitly identifies a target tweet, use `--in-reply-to-tweet-id` to attach the new thread to that tweet.
- Do not invent remote URLs for attachments; always use the provided local workspace file path with `--media-file`.
- If the user provides a single image attachment, do not duplicate it or turn it into a multi-image post.
- If the user did not provide tweet text, do not generate or attach any caption text.
- For a normal standalone image/video post, do not send quote/reply relationship fields.
