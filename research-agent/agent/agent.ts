import { defineAgent, defineDynamic } from "eve";
import { isFreeOssModelEnabled } from "./flags";

const DEFAULT_MODEL = "anthropic/claude-sonnet-5";

/** Free open-weight AI Gateway model (Laguna S 2.1 Free). */
const FREE_OSS_MODEL = "poolside/laguna-s-2.1-free";
const FREE_OSS_CONTEXT_WINDOW_TOKENS = 256_000;

export default defineAgent({
  model: defineDynamic({
    fallback: DEFAULT_MODEL,
    events: {
      "session.started": async () =>
        (await isFreeOssModelEnabled())
          ? {
              model: FREE_OSS_MODEL,
              modelContextWindowTokens: FREE_OSS_CONTEXT_WINDOW_TOKENS,
            }
          : null,
    },
  }),
});
