import { promises as fs } from "node:fs";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(scriptDir, "..");
const skillsDir = path.join(rootDir, "skills");

const allowedFrontmatterFields = new Set([
  "name",
  "description",
  "license",
  "compatibility",
  "metadata"
]);

const allowedTopLevelDirectories = new Set([
  "scripts",
  "references",
  "assets",
  "evals"
]);

const allowedTopLevelFiles = new Set([
  "SKILL.md",
  "LICENSE.txt"
]);

const bannedFiles = new Set([
  "README.md",
  "CHANGELOG.md",
  "INSTALLATION_GUIDE.md",
  "QUICK_REFERENCE.md"
]);

const recommendedMetadataKeys = [
  "owner",
  "status",
  "last-reviewed"
];

const sharedRequiredSections = [
  "Task Fit",
  "Resources to Load",
  "Output Standard",
  "Stop Conditions",
  "Minimal Examples"
];

const skillTypeContracts = {
  normative: {
    requiredSections: [
      "Decision Rules",
      "Exceptions",
      "Conflict Resolution"
    ],
    orderedSections: [
      "Task Fit",
      "Resources to Load",
      "Decision Rules",
      "Exceptions",
      "Conflict Resolution",
      "Output Standard",
      "Stop Conditions",
      "Minimal Examples"
    ]
  },
  tooling: {
    requiredSections: [
      "Preconditions",
      "Standard Procedure",
      "Failure Recovery",
      "Verification"
    ],
    orderedSections: [
      "Task Fit",
      "Resources to Load",
      "Preconditions",
      "Standard Procedure",
      "Failure Recovery",
      "Verification",
      "Output Standard",
      "Stop Conditions",
      "Minimal Examples"
    ]
  },
  process: {
    requiredSections: [
      "Inputs",
      "Workflow",
      "Branches",
      "Quality Gates",
      "Done Definition",
      "Handoff"
    ],
    orderedSections: [
      "Task Fit",
      "Resources to Load",
      "Inputs",
      "Workflow",
      "Branches",
      "Quality Gates",
      "Done Definition",
      "Handoff",
      "Output Standard",
      "Stop Conditions",
      "Minimal Examples"
    ]
  }
};

const evalsTopLevelFields = new Set([
  "$schema",
  "version",
  "skill",
  "trigger_queries",
  "output_cases"
]);

const triggerQueryFields = new Set([
  "query",
  "should_trigger",
  "notes"
]);

const outputCaseFields = new Set([
  "id",
  "prompt",
  "comparison_mode",
  "success_criteria",
  "notes"
]);

const templatePlaceholderPatterns = [
  {
    pattern: /\byour-name\b/i,
    label: '"your-name"'
  },
  {
    pattern: /\bchoose-normative-tooling-or-process\b/i,
    label: '"choose-normative-tooling-or-process"'
  },
  {
    pattern: /\bReplace with\b/,
    label: '"Replace with ..."'
  }
];

const licensePlaceholderText = "Replace this file with the actual license text for the skill.";

const errors = [];
const warnings = [];

main().catch((error) => {
  console.error(`Unexpected validator failure: ${error.message}`);
  process.exitCode = 1;
});

async function main() {
  await ensureDirectory(skillsDir, "Missing skills source directory.");

  const skillNames = await discoverSkillNames(skillsDir);

  if (skillNames.length === 0) {
    warn(skillsDir, "No committed skills found under skills/. The repository skeleton is ready, but no pilot skills are tracked yet.");
  }

  for (const skillName of skillNames) {
    await validateSkill(skillName);
  }

  printSummary(skillNames.length);
  if (errors.length > 0) {
    process.exitCode = 1;
  }
}

async function validateSkill(skillName) {
  const skillDir = path.join(skillsDir, skillName);
  const entries = await fs.readdir(skillDir, { withFileTypes: true });
  const entryNames = new Set(entries.map((entry) => entry.name));

  if (!entryNames.has("SKILL.md")) {
    error(skillDir, "Missing SKILL.md.");
    return;
  }

  if (!entryNames.has("LICENSE.txt")) {
    error(skillDir, "Missing LICENSE.txt.");
  }

  const evalsJsonPath = path.join(skillDir, "evals", "evals.json");
  if (!(await exists(evalsJsonPath))) {
    error(skillDir, "Missing evals/evals.json.");
  }

  for (const entry of entries) {
    if (entry.name.startsWith(".")) {
      continue;
    }

    if (entry.isDirectory() && !allowedTopLevelDirectories.has(entry.name)) {
      warn(path.join(skillDir, entry.name), `Unexpected top-level directory "${entry.name}". Prefer scripts/, references/, assets/, or evals/.`);
    }

    if (entry.isFile() && !allowedTopLevelFiles.has(entry.name)) {
      if (bannedFiles.has(entry.name)) {
        error(path.join(skillDir, entry.name), `Banned file "${entry.name}". Keep human-oriented docs out of skill directories.`);
      } else {
        warn(path.join(skillDir, entry.name), `Unexpected top-level file "${entry.name}". Keep committed skill roots minimal.`);
      }
    }
  }

  const skillFilePath = path.join(skillDir, "SKILL.md");
  const rawSkill = await fs.readFile(skillFilePath, "utf8");

  let parsedSkill;
  try {
    parsedSkill = parseSkillMarkdown(rawSkill);
  } catch (parseError) {
    error(skillFilePath, parseError.message);
    return;
  }

  const skillType = validateFrontmatter(skillName, skillFilePath, parsedSkill.frontmatter);
  validateBody(skillFilePath, parsedSkill.bodyLines, skillType);
  validateTemplatePlaceholders(skillFilePath, rawSkill);

  const licensePath = path.join(skillDir, "LICENSE.txt");
  if (await exists(licensePath)) {
    const rawLicense = await fs.readFile(licensePath, "utf8");
    validateLicense(licensePath, rawLicense);
  }

  if (await exists(evalsJsonPath)) {
    const rawEvals = await fs.readFile(evalsJsonPath, "utf8");
    validateEvals(skillName, evalsJsonPath, rawEvals);
  }
}

function validateFrontmatter(skillName, filePath, frontmatter) {
  for (const key of Object.keys(frontmatter)) {
    if (key === "allowed-tools") {
      error(filePath, 'Frontmatter field "allowed-tools" is not used in v1.');
      continue;
    }

    if (!allowedFrontmatterFields.has(key)) {
      error(filePath, `Unsupported frontmatter field "${key}".`);
    }
  }

  if (!hasNonEmptyString(frontmatter.name)) {
    error(filePath, 'Frontmatter field "name" is required.');
  } else {
    const name = frontmatter.name.trim();
    if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(name)) {
      error(filePath, 'Field "name" must use lowercase letters, digits, and single hyphen separators.');
    }
    if (name.length > 64) {
      error(filePath, 'Field "name" must be 64 characters or fewer.');
    }
    if (name !== skillName) {
      error(filePath, `Field "name" must match the directory name "${skillName}".`);
    }
  }

  if (!hasNonEmptyString(frontmatter.description)) {
    error(filePath, 'Frontmatter field "description" is required.');
  } else {
    const description = frontmatter.description.trim();
    if (!/[\u4e00-\u9fff]/.test(description)) {
      warn(filePath, "Description should be Chinese-first for this repository.");
    }
    if (!/[A-Za-z]/.test(description)) {
      warn(filePath, "Description should keep key English technical terms for discoverability.");
    }
    if (!/(使用|用于|适用|当|when|use)/i.test(description)) {
      warn(filePath, 'Description should explicitly mention when the skill should be used.');
    }
  }

  if (!hasNonEmptyString(frontmatter.license)) {
    error(filePath, 'Frontmatter field "license" is required in this repository.');
  } else if (frontmatter.license.trim() !== "./LICENSE.txt") {
    error(filePath, 'Field "license" must be exactly "./LICENSE.txt" in this repository.');
  }

  if (frontmatter.compatibility !== undefined && !hasNonEmptyString(frontmatter.compatibility)) {
    error(filePath, 'Field "compatibility" must be a non-empty string when present.');
  }

  if (frontmatter.metadata === undefined) {
    error(filePath, 'Frontmatter field "metadata" is required and must include "skill-type".');
    return null;
  }

  if (!isPlainObject(frontmatter.metadata)) {
    error(filePath, 'Field "metadata" must be a mapping of string keys to string values.');
    return null;
  }

  for (const [key, value] of Object.entries(frontmatter.metadata)) {
    if (!hasNonEmptyString(key) || typeof value !== "string") {
      error(filePath, 'Field "metadata" must be a mapping of string keys to string values.');
      return null;
    }
  }

  for (const key of recommendedMetadataKeys) {
    if (!hasNonEmptyString(frontmatter.metadata[key])) {
      warn(filePath, `Metadata key "${key}" is recommended for repository consistency.`);
    }
  }

  if (frontmatter.metadata["last-reviewed"] !== undefined && !/^\d{4}-\d{2}-\d{2}$/.test(frontmatter.metadata["last-reviewed"])) {
    warn(filePath, 'Metadata key "last-reviewed" should use YYYY-MM-DD format.');
  }

  const skillType = frontmatter.metadata["skill-type"];
  if (!hasNonEmptyString(skillType)) {
    error(filePath, 'Metadata key "skill-type" is required.');
    return null;
  }

  if (!Object.prototype.hasOwnProperty.call(skillTypeContracts, skillType)) {
    error(filePath, `Metadata key "skill-type" must be one of: ${Object.keys(skillTypeContracts).join(", ")}.`);
    return null;
  }

  return skillType;
}

function validateBody(filePath, bodyLines, skillType) {
  const nonEmptyLineCount = bodyLines.filter((line) => line.trim().length > 0).length;
  if (nonEmptyLineCount === 0) {
    error(filePath, "SKILL.md must contain body instructions after frontmatter.");
  }

  if (bodyLines.length > 500) {
    warn(filePath, "SKILL.md body is longer than 500 lines. Move detailed material into references/.");
  }

  if (!skillType || !Object.prototype.hasOwnProperty.call(skillTypeContracts, skillType)) {
    return;
  }

  const headingPositions = extractHeadingPositions(bodyLines);
  const requiredSections = [
    ...sharedRequiredSections,
    ...skillTypeContracts[skillType].requiredSections
  ];

  for (const section of requiredSections) {
    if (!headingPositions.has(section)) {
      error(filePath, `Missing required section "${section}" for skill-type "${skillType}".`);
    }
  }

  validateSectionOrder(filePath, headingPositions, skillTypeContracts[skillType].orderedSections);
}

function validateLicense(filePath, rawLicense) {
  if (rawLicense.trim().length === 0) {
    error(filePath, "LICENSE.txt must not be empty.");
  }

  if (rawLicense.includes(licensePlaceholderText)) {
    error(filePath, "LICENSE.txt still contains the template placeholder text.");
  }
}

function validateTemplatePlaceholders(filePath, rawText) {
  for (const { pattern, label } of templatePlaceholderPatterns) {
    if (pattern.test(rawText)) {
      error(filePath, `Template placeholder ${label} must be replaced before committing a formal skill.`);
    }
  }
}

function validateEvals(skillName, filePath, rawEvals) {
  let data;
  try {
    data = JSON.parse(rawEvals);
  } catch (parseError) {
    error(filePath, `Invalid JSON: ${parseError.message}`);
    return;
  }

  if (!isPlainObject(data)) {
    error(filePath, "evals.json must contain a JSON object.");
    return;
  }

  validateUnexpectedFields(filePath, data, evalsTopLevelFields, "evals.json");

  if (typeof data.$schema !== "undefined" && typeof data.$schema !== "string") {
    error(filePath, 'evals.json field "$schema" must be a string when present.');
  }

  if (data.version !== 1) {
    error(filePath, 'evals.json field "version" must be 1.');
  }

  if (data.skill !== skillName) {
    error(filePath, `evals.json field "skill" must match "${skillName}".`);
  }

  if (!Array.isArray(data.trigger_queries)) {
    error(filePath, 'evals.json field "trigger_queries" must be an array.');
  } else {
    if (data.trigger_queries.length < 4) {
      error(filePath, 'evals.json must include at least 4 trigger_queries.');
    }

    const positiveCount = data.trigger_queries.filter((item) => item?.should_trigger === true).length;
    const negativeCount = data.trigger_queries.filter((item) => item?.should_trigger === false).length;

    if (positiveCount < 2 || negativeCount < 2) {
      error(filePath, 'evals.json must include at least 2 should-trigger and 2 should-not-trigger queries.');
    }

    for (const [index, item] of data.trigger_queries.entries()) {
      if (!isPlainObject(item)) {
        error(filePath, `trigger_queries[${index}] must be an object.`);
        continue;
      }

      validateUnexpectedFields(filePath, item, triggerQueryFields, `trigger_queries[${index}]`);

      if (!hasNonEmptyString(item.query)) {
        error(filePath, `trigger_queries[${index}].query must be a non-empty string.`);
      } else if (looksLikeTemplatePrompt(item.query)) {
        error(filePath, `trigger_queries[${index}].query still contains template placeholder text.`);
      }

      if (typeof item.should_trigger !== "boolean") {
        error(filePath, `trigger_queries[${index}].should_trigger must be a boolean.`);
      }

      if (item.notes !== undefined && typeof item.notes !== "string") {
        error(filePath, `trigger_queries[${index}].notes must be a string when present.`);
      }
    }
  }

  if (!Array.isArray(data.output_cases)) {
    error(filePath, 'evals.json field "output_cases" must be an array.');
  } else {
    if (data.output_cases.length < 2) {
      error(filePath, 'evals.json must include at least 2 output_cases.');
    }

    const seenIds = new Set();
    for (const [index, item] of data.output_cases.entries()) {
      if (!isPlainObject(item)) {
        error(filePath, `output_cases[${index}] must be an object.`);
        continue;
      }

      validateUnexpectedFields(filePath, item, outputCaseFields, `output_cases[${index}]`);

      if (!hasNonEmptyString(item.id)) {
        error(filePath, `output_cases[${index}].id must be a non-empty string.`);
      } else {
        if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(item.id)) {
          error(filePath, `output_cases[${index}].id must use lowercase letters, digits, and single hyphen separators.`);
        }

        if (seenIds.has(item.id)) {
          error(filePath, `Duplicate output case id "${item.id}".`);
        }
        seenIds.add(item.id);
      }

      if (!hasNonEmptyString(item.prompt)) {
        error(filePath, `output_cases[${index}].prompt must be a non-empty string.`);
      } else if (looksLikeTemplatePrompt(item.prompt)) {
        error(filePath, `output_cases[${index}].prompt still contains template placeholder text.`);
      }

      if (item.comparison_mode !== "with-vs-without-skill") {
        error(filePath, `output_cases[${index}].comparison_mode must be "with-vs-without-skill".`);
      }

      if (!Array.isArray(item.success_criteria) || item.success_criteria.length < 1) {
        error(filePath, `output_cases[${index}].success_criteria must contain at least one item.`);
      } else {
        for (const [criterionIndex, criterion] of item.success_criteria.entries()) {
          if (!hasNonEmptyString(criterion)) {
            error(filePath, `output_cases[${index}].success_criteria[${criterionIndex}] must be a non-empty string.`);
          } else if (looksLikeTemplatePrompt(criterion)) {
            error(filePath, `output_cases[${index}].success_criteria[${criterionIndex}] still contains template placeholder text.`);
          }
        }
      }

      if (item.notes !== undefined && typeof item.notes !== "string") {
        error(filePath, `output_cases[${index}].notes must be a string when present.`);
      }
    }
  }
}

function validateUnexpectedFields(filePath, objectValue, allowedFields, label) {
  for (const key of Object.keys(objectValue)) {
    if (!allowedFields.has(key)) {
      error(filePath, `${label} contains unsupported field "${key}".`);
    }
  }
}

function extractHeadingPositions(bodyLines) {
  const positions = new Map();

  for (const [index, line] of bodyLines.entries()) {
    const match = /^(#{1,6})\s+(.+?)\s*$/.exec(line);
    if (!match) {
      continue;
    }

    const heading = match[2].trim();
    if (!positions.has(heading)) {
      positions.set(heading, index);
    }
  }

  return positions;
}

function validateSectionOrder(filePath, headingPositions, orderedSections) {
  let previousSection = null;
  let previousPosition = -1;

  for (const section of orderedSections) {
    const currentPosition = headingPositions.get(section);
    if (currentPosition === undefined) {
      continue;
    }

    if (currentPosition < previousPosition) {
      warn(filePath, `Section "${section}" should appear after "${previousSection}" to match the repository contract.`);
      return;
    }

    previousSection = section;
    previousPosition = currentPosition;
  }
}

function looksLikeTemplatePrompt(value) {
  return /^\s*Replace with\b/.test(value);
}

function parseSkillMarkdown(rawText) {
  const lines = rawText.split(/\r?\n/);
  if (lines[0]?.trim() !== "---") {
    throw new Error("SKILL.md must start with YAML frontmatter delimited by ---.");
  }

  let closingIndex = -1;
  for (let index = 1; index < lines.length; index += 1) {
    if (lines[index].trim() === "---") {
      closingIndex = index;
      break;
    }
  }

  if (closingIndex === -1) {
    throw new Error("SKILL.md is missing the closing frontmatter delimiter.");
  }

  const frontmatterLines = lines.slice(1, closingIndex);
  const bodyLines = lines.slice(closingIndex + 1);
  return {
    frontmatter: parseFrontmatter(frontmatterLines),
    bodyLines
  };
}

function parseFrontmatter(lines) {
  const data = {};
  let index = 0;

  while (index < lines.length) {
    const line = lines[index];
    if (line.trim().length === 0) {
      index += 1;
      continue;
    }

    if (/^\s/.test(line)) {
      throw new Error(`Unexpected indentation in frontmatter line: ${line}`);
    }

    const match = /^([A-Za-z0-9_-]+):(?:\s*(.*))?$/.exec(line);
    if (!match) {
      throw new Error(`Unsupported frontmatter line: ${line}`);
    }

    const [, key, rawValue = ""] = match;
    if (Object.prototype.hasOwnProperty.call(data, key)) {
      throw new Error(`Duplicate frontmatter field "${key}".`);
    }

    if (key === "metadata" && rawValue.trim().length === 0) {
      const parsed = parseMetadata(lines, index + 1);
      data[key] = parsed.value;
      index = parsed.nextIndex;
      continue;
    }

    if (rawValue.trim() === "|" || rawValue.trim() === ">") {
      const parsed = parseBlockScalar(lines, index + 1, rawValue.trim());
      data[key] = parsed.value;
      index = parsed.nextIndex;
      continue;
    }

    data[key] = normalizeScalar(rawValue);
    index += 1;
  }

  return data;
}

function parseMetadata(lines, startIndex) {
  const data = {};
  let index = startIndex;

  while (index < lines.length) {
    const line = lines[index];
    if (line.trim().length === 0) {
      index += 1;
      continue;
    }

    if (!line.startsWith("  ")) {
      break;
    }

    const match = /^  ([A-Za-z0-9_.-]+):(?:\s*(.*))?$/.exec(line);
    if (!match) {
      throw new Error(`Unsupported metadata line: ${line}`);
    }

    const [, key, rawValue = ""] = match;
    data[key] = normalizeScalar(rawValue);
    index += 1;
  }

  return { value: data, nextIndex: index };
}

function parseBlockScalar(lines, startIndex, mode) {
  const blockLines = [];
  let index = startIndex;

  while (index < lines.length) {
    const line = lines[index];
    if (line.trim().length === 0) {
      blockLines.push("");
      index += 1;
      continue;
    }

    if (!line.startsWith("  ")) {
      break;
    }

    blockLines.push(line.slice(2));
    index += 1;
  }

  const value = mode === ">" ? foldBlockLines(blockLines) : blockLines.join("\n").trim();
  return { value, nextIndex: index };
}

function foldBlockLines(lines) {
  const paragraphs = [];
  let currentParagraph = [];

  for (const line of lines) {
    if (line === "") {
      if (currentParagraph.length > 0) {
        paragraphs.push(currentParagraph.join(" ").trim());
        currentParagraph = [];
      }
      continue;
    }
    currentParagraph.push(line.trim());
  }

  if (currentParagraph.length > 0) {
    paragraphs.push(currentParagraph.join(" ").trim());
  }

  return paragraphs.join("\n\n").trim();
}

function normalizeScalar(value) {
  const trimmed = value.trim();
  const quotedMatch = /^(['"])(.*)\1$/.exec(trimmed);
  return quotedMatch ? quotedMatch[2] : trimmed;
}

async function discoverSkillNames(sourceDir) {
  const entries = await fs.readdir(sourceDir, { withFileTypes: true });
  return entries
    .filter((entry) => entry.isDirectory() && !entry.name.startsWith("."))
    .map((entry) => entry.name)
    .sort((left, right) => left.localeCompare(right));
}

async function ensureDirectory(directoryPath, failureMessage) {
  if (!(await exists(directoryPath))) {
    throw new Error(`${failureMessage} Expected: ${toRepoPath(directoryPath)}`);
  }
}

async function exists(targetPath) {
  try {
    await fs.access(targetPath);
    return true;
  } catch {
    return false;
  }
}

function hasNonEmptyString(value) {
  return typeof value === "string" && value.trim().length > 0;
}

function isPlainObject(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function toRepoPath(targetPath) {
  return path.relative(rootDir, targetPath).split(path.sep).join("/") || ".";
}

function error(targetPath, message) {
  errors.push(`${toRepoPath(targetPath)}: ${message}`);
}

function warn(targetPath, message) {
  warnings.push(`${toRepoPath(targetPath)}: ${message}`);
}

function printSummary(skillCount) {
  if (errors.length === 0) {
    console.log(`Validated ${skillCount} skill(s) with no blocking errors.`);
  } else {
    console.error(`Validated ${skillCount} skill(s) with ${errors.length} error(s).`);
    for (const issue of errors) {
      console.error(`ERROR: ${issue}`);
    }
  }

  if (warnings.length > 0) {
    for (const issue of warnings) {
      console.warn(`WARN: ${issue}`);
    }
  }
}
