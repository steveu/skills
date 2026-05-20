#!/usr/bin/env node
// Fetch a YouTube video's metadata + English transcript for the `video-note` skill.
//
// Mirrors the proven path in eddy-hq/eddy `src/modules/content/download.ts`
// (`--dump-json` -> `automatic_captions.en` -> json3 URL -> flatten) but with two
// deliberate deltas:
//   1. PRESERVES each line's start time (json3 `tStartMs`) so the skill can emit
//      `[mm:ss]` deep-links. Eddy's flatten throws it away.
//   2. Prefers manual English subtitles over auto-captions when both exist
//      (manual subs are far more accurate; the gist is the re-mineable asset).
//
// This is decoupled from Eddy by design (issue #6): it shells `yt-dlp` directly on
// the M4. It only reads the player response and a public caption file — no video
// download — so it rarely trips YouTube's bot detection.
//
// Usage:  node fetch-transcript.mjs <youtube-url>
//
// Output: one JSON object on stdout describing the result. On success the
//         timestamped transcript is written to a temp file (path in
//         `transcriptFile`) rather than dumped to stdout, to spare the chat
//         context. The skill reads that file, synthesises, then discards it.
//
// Exit:   0 if yt-dlp returned metadata — a transcript may still be absent, so
//         always branch on the `status` field, not the exit code alone.
//         1 on a hard failure (bad URL, unavailable/private video, network).

import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const execFileAsync = promisify(execFile);

const YTDLP_BIN = process.env.YTDLP_BIN || 'yt-dlp';

function out(obj) {
  process.stdout.write(JSON.stringify(obj, null, 2) + '\n');
}

// Map yt-dlp stderr to a clear, terminal reason. Returns null when the failure
// isn't a recognised terminal case (surface the raw stderr instead).
function mapError(stderr) {
  if (/private video|video is private/i.test(stderr)) return 'The video is private.';
  if (/video unavailable|has been removed|no longer available/i.test(stderr)) return "The video isn't available any more.";
  if (/geo.?block|not available in your country/i.test(stderr)) return "The video isn't available in this region.";
  if (/members.?only|join this channel/i.test(stderr)) return 'The video is for channel members only.';
  if (/age.?restrict/i.test(stderr)) return 'The video is age-restricted and needs a signed-in session.';
  if (/premieres? in|premieres? on|this live event will begin|scheduled (start )?time/i.test(stderr)) return "The video hasn't aired yet.";
  if (/sign in to confirm|bot detection|please sign in|not a bot/i.test(stderr)) return 'YouTube returned a bot-detection challenge for this fetch.';
  if (/is not a valid URL|unsupported url/i.test(stderr)) return "That doesn't look like a supported video URL.";
  return null;
}

function humanDuration(secs) {
  if (!secs || secs < 0) return null;
  const h = Math.floor(secs / 3600);
  const m = Math.floor((secs % 3600) / 60);
  const s = Math.floor(secs % 60);
  return h > 0
    ? `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
    : `${m}:${String(s).padStart(2, '0')}`;
}

function stamp(ms) {
  const total = Math.floor(ms / 1000);
  const h = Math.floor(total / 3600);
  const m = Math.floor((total % 3600) / 60);
  const s = total % 60;
  return h > 0
    ? `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
    : `${m}:${String(s).padStart(2, '0')}`;
}

// Flatten YouTube json3 captions to deduplicated, timestamped lines.
//
// Auto-captions arrive as a rolling word-by-word build-up: each phrase is
// re-emitted as a growing prefix until it's complete, then the next phrase
// starts. We collapse that by replacing the in-progress line whenever the new
// text extends it (prefix match), keeping the *first* partial's start time as
// the line's anchor. Manual subtitles don't roll, so each event becomes its own
// line — the same logic handles both.
function flattenJson3(events) {
  const lines = [];
  for (const ev of events || []) {
    const text = (ev.segs || [])
      .map((s) => s.utf8 || '')
      .join('')
      .replace(/\s+/g, ' ')
      .trim();
    if (!text) continue;
    const t = ev.tStartMs ?? 0;
    const prev = lines[lines.length - 1];
    if (prev && (text.startsWith(prev.text) || prev.text.startsWith(text))) {
      // Same rolling phrase growing (or a redundant repeat) — keep the longer
      // text, keep the earliest start time.
      if (text.length > prev.text.length) prev.text = text;
    } else {
      lines.push({ t, text });
    }
  }
  return lines;
}

// Pick the best English caption track: manual subtitles first, then auto-captions.
// Within a track, json3 is required (carries tStartMs).
function pickTrack(json) {
  const langs = ['en', 'en-GB', 'en-US', 'en-orig'];
  for (const [kind, key] of [['manual', 'subtitles'], ['auto', 'automatic_captions']]) {
    const bucket = json[key];
    if (!bucket) continue;
    for (const lang of langs) {
      const tracks = bucket[lang];
      if (!Array.isArray(tracks)) continue;
      const json3 = tracks.find((t) => t.ext === 'json3' && t.url);
      if (json3) return { kind, lang, url: json3.url };
    }
  }
  return null;
}

async function main() {
  const url = process.argv[2];
  if (!url) {
    out({ status: 'error', reason: 'No URL given. Usage: fetch-transcript.mjs <youtube-url>' });
    process.exit(1);
  }

  let stdout;
  try {
    ({ stdout } = await execFileAsync(
      YTDLP_BIN,
      ['--dump-json', '--skip-download', '--no-playlist', '--no-write-playlist-metafiles', url],
      { maxBuffer: 64 * 1024 * 1024 },
    ));
  } catch (err) {
    const stderr = err.stderr || err.message || '';
    if (err.code === 'ENOENT') {
      out({ status: 'error', reason: `yt-dlp not found (looked for "${YTDLP_BIN}").` });
      process.exit(1);
    }
    const reason = mapError(stderr);
    out({ status: 'error', reason: reason || 'yt-dlp failed to fetch the video.', raw: stderr.trim().split('\n').slice(-3).join('\n') });
    process.exit(1);
  }

  let json;
  try {
    json = JSON.parse(stdout);
  } catch {
    out({ status: 'error', reason: 'yt-dlp returned output that was not valid JSON.' });
    process.exit(1);
  }

  if (json.live_status === 'is_live') {
    out({ status: 'error', reason: 'The video is a live broadcast in progress — try again once the stream ends.' });
    process.exit(1);
  }

  const meta = {
    id: String(json.id ?? ''),
    title: String(json.title ?? ''),
    channel: String(json.uploader ?? json.channel ?? ''),
    channelUrl: json.uploader_url ?? json.channel_url ?? null,
    duration: Number(json.duration ?? 0),
    durationHuman: humanDuration(Number(json.duration ?? 0)),
    uploadDate: json.upload_date ?? null, // YYYYMMDD
    webpageUrl: json.webpage_url ?? url,
    description: String(json.description ?? '').slice(0, 1500),
  };

  const track = pickTrack(json);
  if (!track) {
    out({ status: 'no-transcript', reason: 'No English captions (manual or auto) are available for this video.', ...meta });
    process.exit(0);
  }

  let events;
  try {
    const resp = await fetch(track.url);
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    ({ events } = await resp.json());
  } catch (err) {
    out({ status: 'no-transcript', reason: `Found an English ${track.kind} caption track but couldn't fetch it (${err.message}).`, ...meta });
    process.exit(0);
  }

  const lines = flattenJson3(events);
  if (lines.length === 0) {
    out({ status: 'no-transcript', reason: 'The English caption track was empty after parsing.', ...meta });
    process.exit(0);
  }

  const body = lines.map((l) => `[${stamp(l.t)}] ${l.text}`).join('\n');
  const transcriptFile = join(tmpdir(), `video-note-${meta.id || Date.now()}.txt`);
  const header = `# ${meta.title}\n# ${meta.channel}${meta.durationHuman ? ` · ${meta.durationHuman}` : ''}\n# ${meta.webpageUrl}\n# caption track: ${track.kind} (${track.lang})\n\n`;
  writeFileSync(transcriptFile, header + body + '\n', 'utf8');

  out({
    status: 'ok',
    ...meta,
    captionKind: track.kind,
    captionLang: track.lang,
    lineCount: lines.length,
    charCount: body.length,
    transcriptFile,
  });
}

main().catch((err) => {
  out({ status: 'error', reason: err.message });
  process.exit(1);
});
