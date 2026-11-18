# Accounts & saved lists — Firebase setup

The site already has the full accounts system built in (sign-in chip, Google +
email sign-in, and the per-user BEEN / WANT / ★ sync + "My Places" view). It
stays **dormant and invisible** until you paste your Firebase config into
`index.html`. Until then the site works exactly as before (marks save only on
the current device). This takes ~15 minutes, once.

---

## 1. Create a Firebase project
1. Go to <https://console.firebase.google.com> and sign in with your Google account.
2. **Add project** → name it anything (e.g. `best-of-the-best`) → you can disable Google Analytics → **Create project**.

## 2. Register a Web app & copy the config
1. In the project, click the **web** icon `</>` ("Add app").
2. Give it a nickname (e.g. `web`). You do **not** need Firebase Hosting.
3. Firebase shows a `firebaseConfig = { … }` block. Copy those values.
4. Open `index.html`, find `window.BOB_FIREBASE_CONFIG` (search for `PASTE_API_KEY`), and replace every `PASTE_…` value with yours. (Send me the config block and I'll paste it in for you if you'd rather.)

> These config values are **not secrets** — they're meant to live in client code. Your data is protected by the security rules in step 5, not by hiding these.

## 3. Turn on sign-in methods
Firebase console → **Build → Authentication → Get started**, then under **Sign-in method** enable:
- **Google** (pick a support email, Save).
- **Email/Password** (toggle the first switch on, Save).

## 4. Create the database
Firebase console → **Build → Firestore Database → Create database** →
**Start in production mode** → pick a location (e.g. `nam5` / US) → Enable.

## 5. Paste the security rules
Firestore → **Rules** tab → replace everything with this, then **Publish**:

```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Each signed-in user can read & write ONLY their own document.
    match /users/{uid} {
      allow read, write: if request.auth != null && request.auth.uid == uid;
    }
  }
}
```

This guarantees nobody can read or change anyone else's saved places.

## 6. Authorize your domains (for Google sign-in)
Authentication → **Settings → Authorized domains → Add domain**. Add:
- your live domain (e.g. `bestofthebest.xyz` and/or the Netlify `*.netlify.app` URL)

`localhost` is already authorized for local testing.

---

## That's it
Once the config is in and deployed, a **Sign in** chip appears in the top-right of
every banner. Signing in (Google or email) loads that user's saved marks and keeps
them synced; everything they mark as BEEN / WANT / ★ writes to
`users/{their-uid}` in Firestore. The profile dropdown gives them their **Want**,
**Been**, and **ratings** across every city.

### How the data is stored
One document per user at `users/{uid}`, e.g.:

```json
{
  "marks": {
    "chicago|resto|Alinea":   { "m": "been", "r": 5 },
    "newyork|resto|Le Bernardin": { "m": "want", "r": 0 }
  },
  "email": "someone@example.com",
  "updatedAt": 1731900000000
}
```

The key is `city|kind|name`; `m` is `been`/`want`/null, `r` is the 0–5 star rating.

### Free tier
Firebase's free (Spark) plan covers this comfortably — Firestore allows 50K
reads / 20K writes per day and 1 GiB stored. Each visit is ~1 read; each mark is
~1 write. You'd need thousands of daily active users to approach the limits.

### Notes
- Marks made **before** a visitor signs in are folded into their account on first
  sign-in (so nothing they did as a guest is lost). Signing out restores the
  device's own guest marks.
- If a visitor is offline or Firebase is unreachable, marks still save locally and
  sync up next time they're online.
- To wipe the whole thing, just revert the `BOB_FIREBASE_CONFIG` values to the
  `PASTE_…` placeholders — the accounts system goes dormant again.
