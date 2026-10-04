// `detail` command: best-effort full text for a single job by its apply/redirect URL.
import { AdzunaError, fetchDetailText } from "../helpers.ts"

export interface DetailOptions {
  url: string
  format: "plain" | "json"
}

export async function runDetail(opts: DetailOptions): Promise<void> {
  if (!/^https?:\/\//i.test(opts.url)) {
    throw new AdzunaError(
      'detail expects a job URL (the "url" field from a search result), e.g. ' +
        "https://www.adzuna.com/land/ad/123456789",
      "BAD_URL",
    )
  }
  const text = await fetchDetailText(opts.url)
  if (opts.format === "json") {
    process.stdout.write(JSON.stringify({ url: opts.url, text }, null, 2) + "\n")
  } else {
    process.stdout.write(text + "\n")
  }
}
