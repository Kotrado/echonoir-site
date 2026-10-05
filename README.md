# EchonoirAI pipeline

Premise in, story out, narrated, published. Runs on your MacBook with Ollama,
ElevenLabs for the voice, and a built-in static blog plus your own RSS feed for the podcast.
Everything is written into one `site/` folder that you serve from your Mac mini.

```
premise ─▶ outline ─▶ scenes ─▶ polish ─▶ quality checks ─▶ (you read it)
                                                  │
          ElevenLabs narration + ffmpeg finishing ◀┘
                       │
        approve ─▶ podcast feed + blog pages ─▶ upload site/ to the Mac mini
```

## One-time setup

1. `brew install ffmpeg`
2. Make sure Ollama is running and the models in `config.ini` are pulled
   (`ollama pull gemma4:12b`). Your Ollama launcher Shortcut does this.
3. In this folder:
   ```
   cp config.example.ini config.ini
   cp .env.example .env
   ```
4. Edit `.env` (a hidden file; `cp .env.example .env` creates it): paste your `ELEVENLABS_API_KEY`.
   `BEEHIIV_API_KEY` is only needed if you switch the blog backend to beehiiv.
5. Edit `config.ini`:
   - `[elevenlabs] voice_id` (copy from the ElevenLabs voice library)
   - `[show] base_url` and `cover_url`: the public address where the `site/` folder will be served
   - `[publish] command`: how `site/` reaches your Mac mini, e.g.
     `rsync -av --delete {site}/ adriano@macmini.local:/srv/podcast/`
6. Optional: put `intro.mp3`, `outro.mp3` and a square `cover.jpg` (3000x3000 for Apple Podcasts) in `assets/`.
7. `python3 -m echonoir doctor` and fix anything it flags.

On the Mac mini, serve the uploaded folder over HTTPS (Cloudflare Tunnel to a static web server such as
Caddy or nginx), then submit `https://<your domain>/feed.xml` once to Spotify, Apple Podcasts and others.
New episodes appear in the feed automatically afterwards.

## Everyday use

```
python3 -m echonoir new "A night porter finds a room that is not on the plan" --style noir
python3 -m echonoir new --auto --style cosmic          # model invents the premise
python3 -m echonoir list
python3 -m echonoir show <episode>
python3 -m echonoir audio <episode>                    # shows the cost, asks to confirm
python3 -m echonoir approve <episode>                  # podcast feed + blog page, then upload
python3 -m echonoir rebuild-blog                       # regenerate all blog pages and upload
```

Styles: `noir`, `gothic`, `cosmic`, `ghost`. Each has a style card and draws tone-reference
passages from the matching authors in your library folder.

### Flags worth knowing

| Command | What it does |
|---|---|
| `new ... --with-audio` | Also narrates (spends ElevenLabs credits) so you can listen before approving |
| `new ... --auto-publish` | Whole pipeline with no review. Only publishes if every quality check passes; otherwise the episode is held |
| `approve <ep> --no-blog` / `--no-podcast` | Publish only one side |
| `approve <ep> --force` | Publish despite flagged checks (or create another beehiiv post) |
| `rebuild-blog` | Regenerate every blog page, the index and `blog.xml`, then upload |
| `rebuild-feed` | Regenerate `feed.xml` and re-run the upload command |

## Quality checks

A story is held for review (never auto-published) if it is too short or long, contains chatbot text
("As an AI...", "Here is the story"), markdown headings, more than three stock horror phrases,
looping or repeated text, or ends mid-sentence. Failed scenes are regenerated up to
`max_retries` times first. Flagged reasons are listed in the output and in `meta.json`.

## Where things are

```
episodes/<date-title>/   story.txt, meta.json, episode.mp3   (one folder per story)
site/                    everything that gets uploaded:
                           index.html, style.css, blog.xml        the blog
                           stories/<episode>/index.html           one page per story, with audio player
                           feed.xml, episodes/*.mp3, cover.jpg    the podcast
```

## The blog

`[blog] backend = static` (the default) generates a dark, mobile-friendly blog into `site/`: an index,
a page per story with an audio player, prev/next links, and `blog.xml` (full-text RSS). It is rebuilt
from the `episodes/` folder on every `approve`, so a layout change only needs `rebuild-blog`.
Story text is HTML-escaped. To use beehiiv instead, set `backend = beehiiv` and fill in `[beehiiv]`
and `BEEHIIV_API_KEY` (post creation needs beehiiv Pro). `backend = none` publishes the podcast only.

## Tuning

- **Polish pass:** set `polish_model = gemma4:26b` for better prose (needs RAM headroom; lower
  `polish_num_ctx` if it struggles) or `polish = false` to skip it.
- **Length:** `scenes` and `words_per_scene` (default 5 x 500, roughly a 15 minute episode).
- **Voice:** `stability` lower = more expressive, higher = steadier. Try 0.35 to 0.6 for horror.
- **beehiiv (optional backend):** `post_status = confirmed` publishes (and may email subscribers)
  immediately. Keep `draft` until you trust the output.

## Notes

- AI disclosure is added to the blog post and podcast description (`[show] disclosure`). Keep it:
  podcast platforms increasingly expect AI-generated content to be labelled.
- beehiiv's API cannot upload podcast episodes, which is why the podcast is self-hosted here.
- The test suite (`python3 tests/e2e.py`) runs the whole pipeline against mock servers and
  spends nothing.
# echonoir-site
# echonoir-site
# echonoir-site
