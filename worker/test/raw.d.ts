// Vite's ?raw imports: the file's text as a string. The owner tests read the shared cost
// fixtures in ../schema/fixtures/cost/ this way.
declare module "*?raw" {
  const text: string;
  export default text;
}
