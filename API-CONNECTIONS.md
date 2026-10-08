# Where do I put my API keys?

**Part 1 needs no API keys.** Open [START-HERE.html](START-HERE.html) and build your local pages first.

For a later connection, open [the connection helper](API-CONNECTIONS.html). It shows one provider at a time, the exact account screens, where to save the key and how to check the connection.

## Save a key in three steps

1. In the helper, expand **Prepare a private folder**. Copy its complete prompt into the same local Codex or Claude Code project. Your agent creates the hidden private folder and config for you. You do not need to find that folder manually. It gives you the exact command to open your workshop `code/` folder.
2. Open your own terminal. On Mac, press Command + Space and type Terminal. On Windows, use an installed WSL terminal for this program. Paste your agent's folder command, then the Save key command below.
3. Paste your key at the **hidden terminal prompt**, then press Enter. Return to the helper and copy that provider's complete check prompt into your local agent.

Keys belong in private files outside the workshop folder. Do not paste them into chat, this webpage, screenshots, URLs or Git. The helper never accepts a key in the browser.

| Needed | How to get it | Where to save it | What it enables | Check |
|---|---|---|---|---|
| Part 1: none | Your existing local agent account | No key file | Company brief and two local pages | Open and review the pages |
| Part 2: Google | [Google setup steps](API-CONNECTIONS.html#google) | Private desktop-client JSON, then signed-in token | Your mailbox and calendar | Exact sender and primary-calendar read |
| Part 2: ZeroBounce | [API Keys > Create a new API Key](https://www.zerobounce.net/docs/api-dashboard/keys-management) | `keys/zerobounce.key` | Exact email validation | Actual remaining credits |
| Part 3, optional: Loop & Tie | [Request API access and complete OAuth](https://docs.loopandtie.com/reference/oauth-20-api-access) | `keys/loop_and_tie.key` | Meeting-gated email gifts | Owned team, funding and scheduler |
| Part 3, optional: Gojiberry | [Account Settings > API](https://help.gojiberry.ai/en/articles/14540015-using-the-gojiberry-mcp-server) | `keys/gojiberry.key` | Reviewed LinkedIn invitations | Owned seat, list and campaign |
| Part 3, optional: Netlify | [Applications > Personal access tokens](https://docs.netlify.com/api-and-cli-guides/api-guides/get-started-with-api/) | `keys/netlify.key` | Publish one HTML page | Exact site and owner match |

## Exact private paths

The default folder is `~/.local/share/agentic-gtm/workshop-private/`.

- Config: `config.json`. It stores company settings and **key-file paths**, not the key values.
- Provider keys: `keys/PROVIDER.key`. Each file contains only that key.
- Google client download: `google-desktop-client.json`.
- Google signed-in token: the existing login helper saves it under `~/.local/share/agentic-gtm/credentials/` and updates your private config.

Your agent keeps an existing private config if one is already connected. It will give you the exact `--config` path to add to the Save key command. Private folders use permissions 0700; private files use 0600.

## Commands

Run these from the workshop `code/` folder. Pick only the provider you need:

```sh
python3 -B ../save-api-key.py --provider zerobounce
```

For a later session, replace `zerobounce` with `loop_and_tie`, `gojiberry` or `netlify`. Enter only the key value at the hidden prompt, without a `Bearer` prefix.

The key helper saves the file and updates its path. It makes no network call. Copy that provider's **check prompt** from [API-CONNECTIONS.html](API-CONNECTIONS.html) to load the updated config and read the actual account.

Google uses a downloaded OAuth client file, not an API-key string:

```sh
python3 -B gtm.py setup-google \
  --client-file ~/.local/share/agentic-gtm/workshop-private/google-desktop-client.json
```

Sign in with the exact sender in your private config. If your company blocks consent, ask its Workspace administrator to allow the app. Continue building pages and message previews while access is blocked.

## How many validation credits?

Budget one ZeroBounce credit for each unique email address that still needs validation. Your agent removes duplicates and reuses a current valid result when available. Ask it to show the remaining address count and your actual provider balance before you approve the cost. The count comes from your own pilot; it is not always eleven.

## What counts as connected?

`gtm.py ready` checks local setup. It does not prove that every provider works. The provider-specific check must return the actual mailbox, credits or owned resource.

A saved key grants account access. Sending, gift spending and publishing each need a separate exact review in their lesson. Nothing is sent by saving a key.

[Sixtyfour](API-CONNECTIONS.html#sixtyfour) and [Calendly](API-CONNECTIONS.html#calendly) have optional setup steps in the helper. Use them only when you need contact research or already use Calendly. This runtime does not need an OpenAI, Anthropic or OpenRouter model key.

Provider instructions and supplied code checked October 7, 2026.
