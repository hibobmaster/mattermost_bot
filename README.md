## Introduction

This is a simple Mattermost Bot that uses OpenAI's GPT API(or self-host models) to generate responses to user inputs. The bot responds to these commands: `!gpt`, `!chat` and `!new` and  `!help` depending on the first word of the prompt.

## Feature

1. Support Openai ChatGPT
3. ChatGPT web ([pandora](https://github.com/pengzhile/pandora))
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
- `!pic + [prompt]` generate an image from Bing Image Creator

The following commands need pandora http api: https://github.com/pengzhile/pandora/blob/master/doc/wiki_en.md#http-restful-api
- `!talk + [prompt]` chat using chatGPT web with context conversation
- `!goon` ask chatGPT to complete the missing part from previous conversation
- `!new` start a new converstaion

## Demo
Remove support for Bing AI, Google Bard due to technical problems.
![demo1](https://i.imgur.com/XRAQB4B.jpg)
![demo2](https://i.imgur.com/if72kyH.jpg)
![demo3](https://i.imgur.com/GHczfkv.jpg)

## Thanks
<a href="https://jb.gg/OpenSourceSupport" target="_blank">
<img src="https://resources.jetbrains.com/storage/products/company/brand/logos/jb_beam.png" alt="JetBrains Logo (Main) logo." width="200" height="200">
</a>
