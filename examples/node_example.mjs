// Use the proxy from Node 18+ (built-in fetch, no dependency).
//   PROXY=http://localhost:8080 KEY=<your-proxy-key> node examples/node_example.mjs
import { writeFile } from "node:fs/promises";

const PROXY = process.env.PROXY ?? "http://localhost:8080";
const headers = { "X-API-Key": process.env.KEY, "Content-Type": "application/json" };

async function call(path, body) {
  const res = await fetch(`${PROXY}${path}`, { method: "POST", headers, body: JSON.stringify(body) });
  if (!res.ok) throw new Error(`${path}: ${res.status} ${await res.text()}`);
  return res;
}

const chat = await (await call("/v1/chat/completions", {
  model: "gemini-3.8-flash",
  messages: [{ role: "user", content: "Write a one-line slogan for a bakery." }],
})).json();
const slogan = chat.choices[0].message.content.trim();
console.log(slogan);

const img = await (await call("/v1/image", { prompt: `Poster for a bakery: ${slogan}`, aspect_ratio: "3:4" })).json();
await writeFile("bakery.png", Buffer.from(img.data, "base64"));

// Video in two steps: start, then poll.
const { operation } = await (await call("/v1/video", { prompt: "Fresh croissants coming out of a wood oven, steam, close-up", duration_seconds: 4 })).json();
for (;;) {
  await new Promise((r) => setTimeout(r, 15000));
  const status = await (await call("/v1/video/status", { operation })).json();
  if (!status.done) { console.log("rendering..."); continue; }
  if (!status.videos) throw new Error(`No video: ${JSON.stringify(status)}`);
  await writeFile("bakery.mp4", Buffer.from(status.videos[0].data, "base64"));
  break;
}
console.log("Saved bakery.png and bakery.mp4");
