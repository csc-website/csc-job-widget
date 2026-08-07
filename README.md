# CSC Job Widget

A small GitHub Pages widget that displays the five newest jobs from the College Sports Communicators Career Center.

## Source

RSS feed:
https://careercenter.collegesportscommunicators.com/jobs?display=rss

## What it displays

- Five newest jobs
- Bold clickable job title
- Employer beneath the title
- "View job" link
- Compact spacing
- Responsive layout

## GitHub Pages

1. Open the repository's **Settings**.
2. Select **Pages**.
3. Under **Build and deployment**, choose **Deploy from a branch**.
4. Select the `main` branch and `/ (root)`.
5. Click **Save**.
6. GitHub will provide the Pages URL.

The widget URL should be:

https://csc-website.github.io/csc-job-widget/

## Updating the jobs

A GitHub Action runs hourly and can also be run manually from the **Actions** tab.

## Novi AMS iframe

After GitHub Pages is live, use:

<iframe
  src="https://csc-website.github.io/csc-job-widget/"
  width="100%"
  height="400"
  style="border:0;"
  scrolling="yes"
  title="Latest CSC Career Opportunities">
</iframe>

## Important note about the employer field

The update script checks several common RSS field names for the employer and then falls back to the first line of the RSS description. If the CSC feed uses a different field, the employer extraction can be adjusted after the first test run.
