## Introduction

This is a simple Mattermost Bot that uses OpenAI's GPT API(or self-host models) to generate responses to user inputs. The bot responds to these commands: `!gpt`, `!chat` and `!new` and  `!help` depending on the first word of the prompt.

## Feature

1. Support official openai api and self host models([LocalAI](https://localai.io/model-compatibility/))
2. Image Generation with [DALL·E](https://platform.openai.com/docs/api-reference/images/create) or [LocalAI](https://localai.io/features/image-generation/) or [stable-diffusion-webui](https://github.com/AUTOMATIC1111/stable-diffusion-webui/wiki/API)
## Installation and Setup

See https://github.com/hibobmaster/mattermost_bot/wiki

Edit `config.json` or `.env` with proper values

```sh
docker compose up -d
```

## Commands

- `!help` help message
- `!gpt + [prompt]` generate a one time response from chatGPT
- `!chat + [prompt]` chat using official chatGPT api with context conversation
- `!pic + [prompt]` Image generation with DALL·E or LocalAI or stable-diffusion-webui

- `!new` start a new converstaion

## Demo
Remove support for Bing AI, Google Bard due to technical problems.
![gpt command](https://imgur.com/vdT83Ln.jpg)
![image generation](https://i.imgur.com/GHczfkv.jpg)

## Thanks
<a href="https://jb.gg/OpenSourceSupport" target="_blank">
<img src="https://resources.jetbrains.com/storage/products/company/brand/logos/jb_beam.png" alt="JetBrains Logo (Main) logo." width="200" height="200">
</a>
