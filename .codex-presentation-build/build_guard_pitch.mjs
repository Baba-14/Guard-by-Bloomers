import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const workspaceDir = "/Volumes/Baba Disk/Databloom/guard-build";
const buildDir = path.join(workspaceDir, ".codex-presentation-build");
const outputDir = path.join(workspaceDir, "output");
const finalPath = path.join(outputDir, "guard-pitch-product-traction-roadmap.pptx");
const skillDir = "/Users/user/.codex/plugins/cache/openai-primary-runtime/presentations/26.905.11957/skills/presentations";
const runtimePython = "/Users/user/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3";
const { resolvePresentationFont, finalizePresentation } = await import(
  pathToFileURL(path.join(skillDir, "container_tools/artifact_tool_utils.mjs")).href,
);

await fs.mkdir(buildDir, { recursive: true });
await fs.mkdir(outputDir, { recursive: true });

const FONT = resolvePresentationFont({ fontFamily: "Inter 24pt" });
const W = 1280;
const H = 720;
const C = {
  navy: "#071A20",
  navy2: "#0C2730",
  ink: "#102A33",
  blue: "#00A8DB",
  blue2: "#07C6FF",
  pale: "#7FE3FF",
  white: "#FFFFFF",
  mist: "#F3FAFC",
  line: "#D5E8ED",
  muted: "#667C86",
  red: "#EF554F",
  green: "#35C98F",
};

const presentation = Presentation.create({ slideSize: { width: W, height: H } });

function rect(slide, x, y, w, h, fill, radius = 0, line = "none") {
  return slide.shapes.add({
    geometry: radius ? "roundRect" : "rect",
    position: { left: x, top: y, width: w, height: h },
    fill,
    line: { style: "solid", fill: line, width: line === "none" ? 0 : 1 },
    ...(radius ? { borderRadius: radius } : {}),
  });
}

function text(slide, value, x, y, w, h, options = {}) {
  const box = slide.shapes.add({
    geometry: "textbox",
    position: { left: x, top: y, width: w, height: h },
    fill: "none",
    line: { style: "solid", fill: "none", width: 0 },
  });
  box.text = value;
  box.text.style = {
    typeface: FONT,
    fontSize: options.size ?? 24,
    bold: options.bold ?? false,
    color: options.color ?? C.ink,
    alignment: options.align ?? "left",
    verticalAlignment: options.valign ?? "top",
    autoFit: options.autoFit ?? "shrink",
    wrap: "square",
    insets: options.insets ?? { left: 0, right: 0, top: 0, bottom: 0 },
  };
  return box;
}

function line(slide, x, y, w, h, color, width = 2) {
  return slide.shapes.add({
    geometry: "line",
    position: { left: x, top: y, width: w, height: h },
    fill: "none",
    line: { style: "solid", fill: color, width },
  });
}

function numberDot(slide, n, x, y, active = true) {
  const dot = slide.shapes.add({
    geometry: "ellipse",
    position: { left: x, top: y, width: 42, height: 42 },
    fill: active ? C.blue : C.navy2,
    line: { style: "solid", fill: active ? C.blue2 : C.line, width: 1 },
  });
  dot.text = String(n).padStart(2, "0");
  dot.text.style = {
    typeface: FONT, fontSize: 13, bold: true, color: C.white,
    alignment: "center", verticalAlignment: "middle", autoFit: "none",
    insets: { left: 0, right: 0, top: 0, bottom: 0 },
  };
  return dot;
}

function header(slide, title, subtitle, dark = false, page = "") {
  text(slide, title, 64, 44, 900, 56, { size: 38, bold: true, color: dark ? C.white : C.ink });
  if (subtitle) text(slide, subtitle, 66, 100, 930, 46, { size: 17, color: dark ? "#B7D1D9" : C.muted });
  text(slide, `GUARD  ${page}`, 1055, 50, 160, 24, { size: 11, bold: true, color: dark ? C.pale : C.blue, align: "right" });
}

async function imageBytes(relativePath) {
  return new Uint8Array(await fs.readFile(path.join(workspaceDir, relativePath)));
}

// Slide 1: How it works
{
  const slide = presentation.slides.add();
  slide.background.fill = C.navy;
  header(slide, "How Guard works", "A private check produces an explainable result. Only intentional reports enter the learning pipeline.", true, "01");

  const steps = [
    ["Submit", "Message, link, number, screenshot, call or payment request"],
    ["Extract", "Guard detects credential requests, urgency, impersonation and suspicious URLs"],
    ["Corroborate", "Rules and moderated Ghana intelligence strengthen or challenge the signal"],
    ["Explain", "The user receives a risk score, likely pattern and safer next action"],
    ["Improve", "Opt-in reports enter analyst review before they can influence verified intelligence"],
  ];
  line(slide, 86, 178, 0, 394, "#23505D", 3);
  steps.forEach(([label, body], i) => {
    const y = 158 + i * 91;
    numberDot(slide, i + 1, 65, y);
    text(slide, label, 128, y + 2, 155, 28, { size: 19, bold: true, color: C.white });
    text(slide, body, 285, y - 1, 405, 55, { size: 14, color: "#B7D1D9" });
  });

  slide.images.add({
    blob: await imageBytes("public/images/guard-fraud-alert-blue.png"),
    contentType: "image/png",
    alt: "Guard identifying a suspicious mobile payment message",
    fit: "cover",
    position: { left: 738, top: 142, width: 490, height: 492 },
    crop: { left: 0.31, top: 0, right: 0, bottom: 0 },
    geometry: "roundRect",
    borderRadius: 24,
  });
  text(slide, "PRIVATE BY DEFAULT", 760, 600, 210, 26, { size: 11, bold: true, color: C.pale });
  text(slide, "Checks do not become training data unless the user reports them and consents.", 760, 628, 430, 40, { size: 13, color: C.white });
  slide.speakerNotes.textFrame.setText("Product flow based on the current Guard MVP. Private checks remain separate from contributions. Reports require consent and analyst review before promotion into verified intelligence.");
}

// Slide 2: Business model
{
  const slide = presentation.slides.add();
  slide.background.fill = C.mist;
  header(slide, "Business model", "Free access builds reach. Team subscriptions and enterprise integrations fund the intelligence layer.", false, "02");

  const bands = [
    { y: 176, h: 108, width: 500, color: "#DDF7FE", label: "EVERYDAY USERS", price: "Free", copy: "Five checks per day across messages, links and numbers. Guard Plus adds unlimited checks and saved history." },
    { y: 300, h: 128, width: 620, color: "#BEEFFF", label: "SMEs AND SUPPORT TEAMS", price: "GHS 1,500 / month", copy: "Protect includes 2,500 monthly checks, 15 team members, review queues and priority intelligence." },
    { y: 444, h: 148, width: 740, color: "#8BE2FA", label: "ENTERPRISE AND PARTNERS", price: "Custom contracts", copy: "API access, configurable rules, data integrations and dedicated intelligence support." },
  ];
  bands.forEach((band) => {
    rect(slide, 66, band.y, band.width, band.h, band.color, 18, "#9EDBEA");
    text(slide, band.label, 90, band.y + 18, 260, 20, { size: 10, bold: true, color: C.blue });
    text(slide, band.price, 90, band.y + 43, 250, 34, { size: 22, bold: true, color: C.ink });
    text(slide, band.copy, 346, band.y + 20, band.width - 380, band.h - 32, { size: 13, color: C.ink, valign: "middle" });
  });
  text(slide, "LAND", 850, 205, 100, 22, { size: 11, bold: true, color: C.blue });
  text(slide, "Free consumer and team pilots", 850, 232, 290, 40, { size: 18, bold: true, color: C.ink });
  line(slide, 850, 287, 320, 0, C.line, 2);
  text(slide, "EXPAND", 850, 320, 100, 22, { size: 11, bold: true, color: C.blue });
  text(slide, "More checks, seats and shared workflows", 850, 347, 300, 50, { size: 18, bold: true, color: C.ink });
  line(slide, 850, 416, 320, 0, C.line, 2);
  text(slide, "INTEGRATE", 850, 448, 120, 22, { size: 11, bold: true, color: C.blue });
  text(slide, "API, custom rules and partner data", 850, 475, 300, 50, { size: 18, bold: true, color: C.ink });
  rect(slide, 850, 554, 310, 48, C.navy, 12);
  text(slide, "Recurring subscriptions + enterprise contracts", 866, 568, 278, 22, { size: 12, bold: true, color: C.white, align: "center" });
  text(slide, "Current product pricing. Enterprise pricing varies by volume and integration scope.", 68, 650, 800, 24, { size: 11, color: C.muted });
  slide.speakerNotes.textFrame.setText("Pricing source: Guard product pages in app/pricing/page.tsx and app/business/page.tsx, reviewed 17 October 2026. Enterprise pricing remains custom and should be tested through pilots.");
}

// Slide 3: Traction
{
  const slide = presentation.slides.add();
  slide.background.fill = C.navy;
  header(slide, "Traction", "The MVP now connects research, user experience, risk logic and a governed data pipeline.", true, "03");

  const metrics = [
    ["7", "input types", "Messages, links, numbers, WhatsApp, screenshots, calls and payments"],
    ["1,400", "records loaded", "Fraud, legitimate and URL examples in the intelligence dataset"],
    ["26", "analysis tests", "Core pattern, URL, database and safety checks passing"],
  ];
  metrics.forEach(([value, label, detail], i) => {
    const x = 68 + i * 390;
    text(slide, value, x, 164, 220, 74, { size: 52, bold: true, color: C.blue2 });
    text(slide, label, x, 232, 220, 26, { size: 16, bold: true, color: C.white });
    text(slide, detail, x, 267, 310, 52, { size: 12, color: "#AFCAD2" });
  });
  line(slide, 68, 337, 1144, 0, "#24444E", 2);

  text(slide, "DISCOVERY AND DESIGN", 68, 374, 330, 22, { size: 11, bold: true, color: C.pale });
  text(slide, "User research and problem definition\nGhana fraud-pattern mapping\nPublic product flows and admin workspace\nResponsive screens and brand system", 68, 410, 480, 168, { size: 18, color: C.white });

  text(slide, "WORKING SYSTEM", 650, 374, 300, 22, { size: 11, bold: true, color: C.pale });
  text(slide, "Explainable risk engine and URL analysis\nFastAPI backend with Supabase PostgreSQL\nAuthentication and role-based administration\nReporting, import and analyst review pipeline", 650, 410, 500, 168, { size: 18, color: C.white });

  rect(slide, 68, 615, 1082, 3, C.blue);
  text(slide, "Current stage", 68, 636, 130, 22, { size: 11, bold: true, color: C.pale });
  text(slide, "Working MVP ready for controlled pilots and verified Ghana data partnerships", 205, 633, 900, 30, { size: 18, bold: true, color: C.white });
  slide.speakerNotes.textFrame.setText("Internal product status as of 17 October 2026. Metrics describe product implementation, test coverage and dataset records. They do not represent active users, revenue or validated commercial traction.");
}

// Slide 4: Milestones
{
  const slide = presentation.slides.add();
  slide.background.fill = C.white;
  header(slide, "Key milestones", "A proposed quarterly path from working MVP to repeatable deployment by the end of 2027.", false, "04");

  const quarters = [
    ["Q4 2026", "Foundation", "User research complete\nWeb MVP, backend and database working", C.green],
    ["Q1 2027", "Pilot readiness", "Review and benchmark the dataset\nOnboard controlled SME and support-team pilots", C.blue],
    ["Q2 2027", "Multi-channel beta", "Release the mobile app beta\nTest browser extension and partner plugin", C.blue],
    ["Q3 2027", "Partnerships and data", "Secure cybersecurity and sector partners\nExpand verified Ghana fraud intelligence", C.blue],
    ["Q4 2027", "Scale readiness", "Run paid enterprise pilots\nHarden API, security and model monitoring", C.blue],
  ];
  line(slide, 104, 252, 1050, 0, C.line, 5);
  quarters.forEach(([quarter, title, body, color], i) => {
    const x = 84 + i * 230;
    const dot = slide.shapes.add({
      geometry: "ellipse",
      position: { left: x + 68, top: 230, width: 44, height: 44 },
      fill: color,
      line: { style: "solid", fill: C.white, width: 4 },
    });
    dot.text = String(i + 1);
    dot.text.style = { typeface: FONT, fontSize: 14, bold: true, color: C.white, alignment: "center", verticalAlignment: "middle", autoFit: "none", insets: { left: 0, right: 0, top: 0, bottom: 0 } };
    text(slide, quarter, x, 175, 180, 26, { size: 14, bold: true, color });
    text(slide, title, x, 298, 190, 50, { size: 20, bold: true, color: C.ink });
    text(slide, body, x, 365, 190, 145, { size: 14, color: C.muted });
    if (i === 0) {
      rect(slide, x, 533, 92, 28, "#DDF7EE", 14);
      text(slide, "COMPLETED", x + 8, 541, 76, 14, { size: 9, bold: true, color: "#16705C", align: "center" });
    } else {
      rect(slide, x, 533, 84, 28, "#E7F7FC", 14);
      text(slide, "PROPOSED", x + 8, 541, 68, 14, { size: 9, bold: true, color: C.blue, align: "center" });
    }
  });
  rect(slide, 68, 611, 1144, 54, C.navy, 14);
  text(slide, "2027 outcome", 92, 628, 140, 20, { size: 11, bold: true, color: C.pale });
  text(slide, "Verified local intelligence, multi-channel access and enterprise pilots ready for scale", 245, 624, 900, 28, { size: 18, bold: true, color: C.white });
  slide.speakerNotes.textFrame.setText("Q4 2026 reflects completed internal work. All 2027 milestones are proposed planning assumptions and should be revised after pilot partner commitments, data-access agreements and resourcing decisions.");
}

// Slide 5: The ask
{
  const slide = presentation.slides.add();
  slide.background.fill = C.navy;
  slide.images.add({
    blob: await imageBytes("public/images/guard-hero-ghana-government.png"),
    contentType: "image/png",
    alt: "Ghanaian cybersecurity team reviewing fraud intelligence",
    fit: "cover",
    position: { left: 665, top: 0, width: 615, height: 720 },
    crop: { left: 0.26, top: 0, right: 0, bottom: 0 },
  });
  rect(slide, 0, 0, 760, 720, C.navy);
  text(slide, "The ask", 64, 50, 500, 55, { size: 40, bold: true, color: C.white });
  text(slide, "Partners can help Guard move from a working MVP to controlled Ghana pilots.", 66, 112, 560, 58, { size: 18, color: "#B7D1D9" });
  text(slide, "GUARD  05", 1070, 50, 145, 24, { size: 11, bold: true, color: C.pale, align: "right" });

  const asks = [
    ["01", "Cybersecurity partnerships", "Fraud expertise, threat intelligence and independent evaluation from trusted security organisations."],
    ["02", "Privacy-safe Ghanaian data", "De-identified messages, URLs, sender patterns and confirmed cases from telcos, banks, fintechs and agencies."],
    ["03", "Cloud and model credits", "Compute, secure storage, model inference, monitoring and evaluation support for the pilot period."],
    ["04", "Pilot distribution", "Access to SMEs, merchants, support teams and public-sector services where Guard can test real workflows."],
  ];
  asks.forEach(([n, title, body], i) => {
    const y = 198 + i * 105;
    text(slide, n, 68, y, 40, 24, { size: 12, bold: true, color: C.blue2 });
    text(slide, title, 120, y - 2, 410, 30, { size: 19, bold: true, color: C.white });
    text(slide, body, 120, y + 32, 500, 58, { size: 13, color: "#B7D1D9" });
    if (i < asks.length - 1) line(slide, 120, y + 92, 490, 0, "#24444E", 1);
  });
  rect(slide, 66, 628, 558, 48, C.blue, 12);
  text(slide, "Priority: launch trusted pilots with verified Ghana fraud intelligence", 82, 642, 526, 21, { size: 13, bold: true, color: C.white, align: "center" });
  slide.speakerNotes.textFrame.setText("Partnership asks reflect the priorities supplied by the founder: cybersecurity partnerships, cloud or model credits, pilot distribution and access to privacy-safe Ghanaian fraud data. No funding amount is stated because the capital requirement has not yet been defined.");
}

const candidatePath = path.join(buildDir, "guard-pitch-candidate.pptx");
await (await PresentationFile.exportPptx(presentation)).save(candidatePath);

for (let i = 0; i < presentation.slides.items.length; i += 1) {
  const preview = await presentation.export({ slide: presentation.slides.items[i], format: "png", scale: 1 });
  await fs.writeFile(path.join(buildDir, `draft-slide-${i + 1}.png`), new Uint8Array(await preview.arrayBuffer()));
}

const requirements = {
  explicitTotalSlideCount: 5,
  requiredNativeTableOwnerSlides: [],
  requiredNativeChartOwnerSlides: [],
};
const fontPolicy = { basis: "user_request", families: [FONT] };
const stagingDir = path.join(buildDir, "finalizer");
await fs.mkdir(stagingDir, { recursive: true });
const result = await finalizePresentation({
  ...requirements,
  workspaceDir,
  candidatePath,
  finalPath,
  pythonExecutable: runtimePython,
  integrityValidatorPath: path.join(skillDir, "container_tools/inspect_presentation_package_integrity.py"),
  layoutValidatorPath: path.join(skillDir, "container_tools/inspect_presentation_layout_geometry.py"),
  layoutArgs: [
    "--expected-slide-size-emu", "12192000,6858000",
    "--validate-bullet-geometry",
    "--validate-heading-fit",
  ],
  requiredNativeTableOwnerSlides: [],
  fontPolicy,
  verifyArtifactToolImport: true,
  receiptPath: path.join(stagingDir, "guard-pitch.validation.json"),
});

console.log(JSON.stringify({ finalPath, font: FONT, result }, null, 2));
