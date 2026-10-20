# Free scheduled cloud setup

This repository can run as a scheduled GitHub Actions job on a GitHub-hosted Ubuntu runner. Your MacBook does not need to stay on.

## What this setup does

- Runs once per day automatically, and can also be started manually for 1–5 videos.
- Installs FFmpeg and the Python dependencies in a clean Linux environment.
- Downloads `utils/gameplay.mp4` from a direct-download URL stored as a GitHub Actions secret.
- Uses Whisper `base.en` on CPU by default for more practical cloud runtime. Set `WHISPER_MODEL` in the workflow if you intentionally want a slower/larger model.
- Uploads generated MP4s as a downloadable Actions artifact, retained for 14 days.
- Commits the updated counter so later scheduled runs advance through `utils/stories.json`.

## One-time setup

1. Push these files to the **default branch** of your GitHub repository. Keep the repository private if you do not want the story content and source code public.
2. Upload your gameplay file to a place that can provide a **direct file-download URL**. It must return the MP4 bytes when fetched with `curl -L`, not an HTML preview page. Keep the video file itself private if possible and use a long-lived signed download URL if the host supports it.
3. In GitHub, open **Settings → Secrets and variables → Actions → New repository secret** and add:
   - `TTS_API_KEY`: your Lemonfox API key.
   - `GAMEPLAY_VIDEO_URL`: the direct-download URL for your gameplay MP4.
4. Open **Settings → Actions → General** and ensure the workflow has permission to read and write repository contents. The workflow also declares `contents: write`.
5. Open **Actions → Generate Reddit videos → Run workflow** and select 1–5 videos to test it. Download the MP4 from the run's Artifacts section.
6. Once the manual run succeeds, the scheduled job will run daily at 18:17 UTC. Scheduled jobs may start late, and GitHub may disable schedules on inactive public repositories.

## Important limitations and known project fixes

- The uploaded ZIP did not contain `utils/gameplay.mp4`; it is ignored by `.gitignore`, so the workflow downloads it from `GAMEPLAY_VIDEO_URL`.
- Do not upload `.env` or API keys to Git. `.env.example` is only a template.
- The original code hard-coded a Windows ImageMagick path and CUDA. The cloud version removes the ImageMagick dependency and automatically selects CUDA if available, otherwise CPU.
- The original story counter used `count += 0`, so it never advanced. It now increments properly. If the counter passes the number of entries in `utils/stories.json`, the code cycles back to the start. **The provided ZIP currently contains only one story**, so add more entries to `utils/stories.json` if you want distinct videos rather than repeated versions of the same story.
- Cloud runner CPU encoding and Whisper can take a while. The free tier is not an always-on server. Public repositories can use standard GitHub-hosted runners without Actions-minute charges; private repositories have a monthly included quota (currently 2,000 minutes for GitHub Free), and artifact storage is limited. Check current limits before increasing frequency.
- Lemonfox TTS usage may have its own quota or cost; GitHub Actions being free does not make the external TTS API free.

## Local Mac or Windows use

Install FFmpeg, install the packages from `requirements.txt`, set `TTS_API_KEY` in your environment (or a local `.env`), put the gameplay video at `utils/gameplay.mp4`, then run `python main.py`. On local hardware you can set `WHISPER_MODEL=medium.en` if you prefer the original model and have enough memory.
