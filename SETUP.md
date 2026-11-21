# Set up your GitHub profile — SantoshThkr

This is a complete replacement for the README in **https://github.com/SantoshThkr/SantoshThkr**.

## What it includes

- `README.md`: profile introduction, links, projects, technical stack, analytics sections
- `assets/hero.svg`: the custom header graphic
- `assets/projects/*.svg`: four project cards (each links to a real repository or your repo list)
- `assets/analytics/*.svg`: four locally hosted analytics images
- `scripts/generate_analytics.py`: Python (standard library only) that reads GitHub's API and produces real stats
- `.github/workflows/profile-analytics.yml`: automatic refresh workflow

**No paid service, external stats widget, or manually created personal access token is required.**

## Publish it

1. Download and extract the ZIP file.
2. Open the **public** profile repository: https://github.com/SantoshThkr/SantoshThkr
3. Upload the extracted contents **into the root of that repository**, replacing `README.md`. Preserve `.github/workflows/`, `scripts/`, and `assets/` folders. Hidden `.github` folders must be included.
4. Check **Settings → Actions → General → Workflow permissions**. If necessary and available, allow **Read and write permissions** for the repository's GitHub Actions workflows. The workflow requests `contents: write`; organization/repository settings can override it.
5. In the **Actions** tab, open **Refresh GitHub profile analytics** and choose **Run workflow**. The workflow is also configured to run on changes to its script/workflow and daily at **03:23 UTC**.
6. After a successful run, refresh your GitHub profile. The placeholder chart messages will become real numeric dashboards.

## What the charts actually measure

- **Public repos**: public repositories that you own, including your public forks.
- **Repo stars**: stars received by the public repositories you own (not the repos you personally starred).
- **Contributions/year**: contribution-calendar total from GitHub's default last-year collection (can include more than commits).
- **Commits/year**: eligible commit contributions counted by GitHub in that same last-year collection, not every git commit ever made.
- **Streaks**: contribution days in the recent year's calendar, including today or yesterday as appropriate. The *best streak/year* is not your lifetime record.
- **Weekly activity**: all calendar contributions by week, **not** commits only.
- **Commit activity**: `totalCommitContributions` queried separately for each of the last 12 calendar months. The current month is incomplete.
- Private contributions require particular GitHub visibility settings and token access; the bundled GITHUB_TOKEN should be treated as **public-data-only**.

## Reliability and limitations

- All displayed images are stored **in your own repository**. This avoids depending on a public stats-card server that may rate-limit or be discontinued.
- The included chart images start with honest placeholders, so nothing displays false metrics before the first successful run.
- If the main API query fails, existing chart images remain unchanged. If only the monthly commit query fails, the other three images still refresh, and the existing commit chart is retained.
- GitHub scheduled Actions can be delayed. On public repositories with no activity for 60 days, GitHub can **disable scheduled workflows**. Re-enable the workflow from the Actions tab or update its schedule. Manual runs remain an option.
- Repository branch protection, organization policy, or limited token permissions may stop the workflow from pushing SVGs; if this occurs, adjust repository workflow permissions or use a permitted branch/PR process.
- If an SVG looks old after refreshing, it may be cached by GitHub's image proxy. Try again after the cache expires.
- The script needs network access to `api.github.com` and does not function offline without test mocks.

## Personalization

- Project names and their links were checked against your public repositories. Update descriptions as projects evolve.
- The header and project images are standalone SVGs. You can change their text/colors by editing the files directly.
- Your email, LinkedIn and portfolio are included based on the details you supplied; update them in `README.md` if they change.

**Security:** Never paste a token or secret into `README.md`, the workflow, or your public repository. The workflow uses the built-in `secrets.GITHUB_TOKEN` automatically.
