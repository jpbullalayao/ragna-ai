import { flagsClient } from "@vercel/flags-core";

/** Dashboard: https://vercel.com/jpbullalayaos-projects/ragna-research/flag/free-oss-model */
export const FREE_OSS_MODEL_FLAG = "free-oss-model";

let initializePromise: Promise<void> | undefined;

async function ensureFlagsInitialized(): Promise<void> {
  initializePromise ??= Promise.resolve(flagsClient.initialize()).then(() => undefined);
  await initializePromise;
}

/** Whether to route the agent through the free open-source AI Gateway model. */
export async function isFreeOssModelEnabled(): Promise<boolean> {
  await ensureFlagsInitialized();
  const result = await flagsClient.evaluate<boolean>(FREE_OSS_MODEL_FLAG, false);
  return result.value === true;
}
