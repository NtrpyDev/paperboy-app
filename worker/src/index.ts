import { createHandler } from "./handler";

export default createHandler({
  fetch: (input, init) => fetch(input, init),
  now: () => Date.now(),
}) satisfies ExportedHandler<Env>;
