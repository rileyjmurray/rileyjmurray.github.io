# Notes: short posts from a phone

Notes are short, untitled posts that live in `_notes/` and appear at
[/notes/](https://rileymurray.ai/notes/), each with its own permalink and an
Atom feed at `/notes/feed.xml`. Long-form writing stays in `_posts/` (the blog).

This file explains how notes work on the site and how to build the iOS
Shortcut that previews and publishes them.

## How notes work

A note is a Markdown file named `_notes/YYYY-MM-DD-HHMMSS.md`:

```markdown
---
date: 2026-10-02T20:45:12-07:00
---

A sketch $$S$$ with $$\|SAx\|_2 \approx \|Ax\|_2$$ for all $$x$$ is a _subspace embedding_.
```

- **URL.** The note above is published at `/notes/2026/10/02/204512/`.
- **Front matter.** Only `date` is required. Optional fields are `tags: [rnla, software]`
  and `title:`. A plugin (`_plugins/notes.rb`) derives the browser-tab title,
  feed title, and search text from the note's first words, so you rarely need `title:`.
- **Math.** Use `$$...$$`, the same as in blog posts. Inline `$$...$$` renders
  inline; `$$` on its own lines renders as display math.
- **Images.** Commit the image under `assets/img/notes/` and reference it with
  `![](/assets/img/notes/name.jpg)`. The Shortcut below doesn't handle photos yet.
- **Drafts** live in `_note_drafts/`. Jekyll ignores that folder, and the deploy
  workflow doesn't run when only drafts change. The repository is public, so
  drafts are visible to anyone browsing the source on GitHub.
- **Editing or deleting** a published note: edit or delete its file in
  `_notes/` (from your laptop, or on github.com from your phone).

Configuration lives in `_config.yml`: `notes_name`, `notes_description`, the
`notes` collection, and `feed.collections.notes`.

### The preview page

`/notes/preview/` renders a note passed in the URL fragment:
`https://rileymurray.ai/notes/preview/#<base64 of the Markdown>`. The fragment
is never sent to the server, so a draft isn't sent anywhere when you preview it.
The page renders Markdown in the browser with [marked](https://marked.js.org/),
handles `$$...$$` the way kramdown does, and then runs MathJax. For ordinary
note content it matches the built site. Kramdown-only syntax, such as `{:.class}`
attribute lists, will differ. The page is excluded from search engines and the
sitemap.

## The iOS Shortcut

The Shortcut is called **Note**. When you run it, it asks whether to start a
new note or continue a draft. Then it:

1. Lets you write or dictate the text.
2. Shows the preview page.
3. Offers **Publish**, **Edit**, **Save as draft**, or **Cancel**.

**Edit** reopens the text with your draft filled in and previews it again.
**Publish** commits to `_notes/` (and deletes the draft file, if there was
one), and the site redeploys in a few minutes.

### 1. Create a GitHub token

On github.com: **Settings → Developer settings → Personal access tokens →
Fine-grained tokens → Generate new token**.

- **Token name:** `notes shortcut`
- **Expiration:** your choice (e.g. one year). Put a renewal reminder in your calendar.
- **Repository access:** Only select repositories → `rileyjmurray/rileyjmurray.github.io`
- **Permissions → Repository permissions → Contents:** Read and write.
  Leave everything else as is (GitHub adds Metadata: Read-only automatically).

Copy the token (`github_pat_...`). It goes in the Shortcut's first action.
Anyone with the token can commit to this one repository, so don't share the
Shortcut once the token is in it.

### 2. Build the Shortcut

In the Shortcuts app, create a new shortcut named **Note**. The steps below
use these names for variables (**Set Variable**) and use these shared settings
for every **Get Contents of URL** action:

- **Headers:**
  - `Authorization`: `Bearer ` followed by the **Token** variable
  - `Accept`: `application/vnd.github+json`, except where a step says otherwise
  - `X-GitHub-Api-Version`: `2022-11-28`

Each **Get Contents of URL** request is to `[API]/<path>`, where **API** is
the variable set in step 2.

**Setup**

1. **Text**: your token. **Set Variable** `Token`.
2. **Text**: `https://api.github.com/repos/rileyjmurray/rileyjmurray.github.io/contents`.
   **Set Variable** `API`.

**Get the note text.** When **Edit** reruns the Shortcut, it passes the text
in. Otherwise, start fresh.

3. **If** `Shortcut Input` **has any value**.
   Using `Shortcut Input` adds a "Receive **Any** input from **Nowhere**"
   header at the top of the Shortcut. Leave that header as is.
   - **Get Dictionary Value** `text` in `Shortcut Input` → **Set Variable** `Body`
   - **Get Dictionary Value** `draft` in `Shortcut Input` → **Set Variable** `Draft`
   - **Get Dictionary Value** `sha` in `Shortcut Input` → **Set Variable** `SHA`
4. **Otherwise**:
   - **Choose from Menu** with prompt `Note`, items **New note** and **Continue a draft**.
   - Under **New note**:
     - **Ask for Input**: Text, prompt `Note`, **Allow Multiple Lines** on → **Set Variable** `Body`
   - Under **Continue a draft**:
     - **Get Contents of URL** `[API]/_note_drafts` (GET).
     - **Repeat with Each** item in `Contents of URL`:
       - **Get Dictionary Value** `name` in `Repeat Item`
       - **If** `Dictionary Value` **ends with** `.md` → **Add to Variable** `DraftNames`
       - **End If**
     - **End Repeat**
     - **If** `DraftNames` **does not have any value** → **Show Alert** `No drafts`, then **Stop This Shortcut**. **End If**
     - **Choose from List** `DraftNames` → **Set Variable** `Draft`
     - **Get Contents of URL** `[API]/_note_drafts/[Draft]` (GET) →
       **Get Dictionary Value** `sha` → **Set Variable** `SHA`
     - **Get Contents of URL** `[API]/_note_drafts/[Draft]` (GET), with the
       `Accept` header set to `application/vnd.github.raw+json` → **Set Variable** `Body`
   - **End Menu**
5. **End If**

**Preview**

6. **Base64 Encode** `Body`, with **Line Breaks** set to **None** → **Set Variable** `Encoded`.
7. **URL**: `https://rileymurray.ai/notes/preview/#[Encoded]`
8. **Show Web Page** at `URL`. Tap **Done** when you have read it.

**Decide**

9. **Current Date** → **Format Date** with a custom format `yyyy-MM-dd-HHmmss` →
   **Set Variable** `Stamp`.
10. **Choose from Menu** with prompt `Publish this note?`, items **Publish**,
    **Edit**, **Save as draft**, **Cancel**.

Under **Publish**:

- **Current Date** → **Format Date**: **ISO 8601**, with **Include ISO 8601 Time** on → **Set Variable** `When`
- **Text** (three lines of front matter, then the body):
  ```
  ---
  date: [When]
  ---
  [Body]
  ```
- **Base64 Encode** that text with **Line Breaks** set to **None** → **Set Variable** `File`
- **Get Contents of URL** `[API]/_notes/[Stamp].md`, **Method** PUT,
  **Request Body** JSON with Text fields `message` = `Add note` and
  `content` = `File`
- **Get Dictionary Value** `commit` in `Contents of URL`.
  **If** it **does not have any value** → **Show Alert** with `Contents of URL`
  (GitHub's error message), then **Stop This Shortcut**. **End If**
- **If** `Draft` **has any value** → **Get Contents of URL**
  `[API]/_note_drafts/[Draft]`, **Method** DELETE, **Request Body** JSON with
  `message` = `Publish draft` and `sha` = `SHA`. **End If**
- **Show Notification** `Published. Live in a few minutes.`

Under **Edit**:

- **Ask for Input**: Text, prompt `Note`, **Default Answer** `Body`,
  **Allow Multiple Lines** on
- **Dictionary** with Text entries `text` = `Provided Input`, `draft` = `Draft`,
  `sha` = `SHA`
- **Run Shortcut** `Note` with input `Dictionary`
- **Stop This Shortcut**

Under **Save as draft**:

- **Base64 Encode** `Body` with **Line Breaks** set to **None** → **Set Variable** `File`
- **If** `Draft` **has any value** (updating an existing draft):
  - **Get Contents of URL** `[API]/_note_drafts/[Draft]`, **Method** PUT,
    **Request Body** JSON with `message` = `Update note draft`,
    `content` = `File`, and `sha` = `SHA`
- **Otherwise** (a new draft):
  - **Get Contents of URL** `[API]/_note_drafts/[Stamp].md`, **Method** PUT,
    **Request Body** JSON with `message` = `Add note draft` and `content` = `File`
- **End If**
- **Get Dictionary Value** `commit` in `If Result`.
  **If** it **does not have any value** → **Show Alert** `If Result`, then
  **Stop This Shortcut**. **End If**
- **Show Notification** `Draft saved.`

Under **Cancel**:

- **Stop This Shortcut**

11. **End Menu**

Add the Shortcut to your home screen or Action button. To dictate, tap the
keyboard's microphone in the **Ask for Input** box.

### Troubleshooting

- **The alert says "Bad credentials".** The token expired or was mistyped.
  Make a new one and paste it into step 1.
- **The alert says "sha wasn't supplied" or "does not match".** The draft changed
  somewhere else after you opened it. Run the Shortcut again and continue the draft.
- **The note isn't on the site.** Check the **Deploy site** run under the
  repository's **Actions** tab. A build usually takes a few minutes.
