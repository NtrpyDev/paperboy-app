# Glossary

The words this project uses, one meaning each.

- **Paper**: one scientific work, whether a preprint or a peer-reviewed article. Identified by a stable **paper id** built from its DOI or arXiv id.
- **Badge**: the label saying what kind of paper it is: `PREPRINT` or `PEER-REVIEWED`.
- **Feed**: the endless list of papers the app shows, newest and best first.
- **Card**: one paper as it appears in the feed. An **explained card** has a hero image and opens an explainer. A **short card** has only a summary and a link to the paper; paywalled papers and papers not yet explained are short cards.
- **Hook**: the one-line plain-language headline on a card. Not the paper's title.
- **Summary**: the two to four plain sentences on a card, written by the pipeline. Never the paper's abstract.
- **Explainer**: the interactive page that teaches one paper visually. One HTML document per paper.
- **Hero**: the showpiece visual at the top of an explainer. Its still image is the card image.
- **Kit**: the shared stylesheet and script every explainer loads. Versioned (`kit/v1`); old versions stay served forever.
- **Rating**: a reader's "more like this" or "less like this" on a card. Stored only on the phone.
- **Taste**: the on-device model learned from ratings that reorders the feed for one reader.
- **Chunk**: one numbered file of feed items. Chunks fill in order; a full chunk never changes.
- **Head**: the small file that says how many chunks exist. The app reads it first.
- **Content repo**: the public git repository holding published explainers, chunks, and pipeline state (`NtrpyDev/paperboy-content`).
- **Pipeline**: everything that turns newly released papers into feed items and explainers.
- **Run**: one execution of the pipeline in a cloud routine.
- **Scout**: the pipeline agent that finds new papers and judges which are worth showing.
- **Expert**: the pipeline agent that reads one paper as a specialist in its field and writes the brief.
- **Brief**: the expert's structured account of one paper: the question, method, findings with exact numbers and where they appear, limits, and what to visualize.
- **Visualizer**: the pipeline agent that builds the explainer from the brief.
- **Checker**: the pipeline agent that verifies an explainer against the paper and judges whether its visuals are clear. Independent of the visualizer.
- **Render check**: the automated part of checking: loading the explainer in a headless browser and failing on script errors, overflow, or missing parts.
- **Usage gate**: the rule that stops a run when the Claude subscription's weekly usage reaches 50 percent.
- **Content base**: the web address the app loads the feed and explainers from.
