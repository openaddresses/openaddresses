# OpenAddresses GitHub Agents

This directory contains specialized GitHub Agent files that help automate tasks in the OpenAddresses repository.

## What are GitHub Agents?

GitHub Agents are AI-powered assistants with specialized knowledge and instructions for specific tasks. They are invoked through GitHub Copilot and can autonomously perform complex workflows.

## Available Agents

### Source Updater Agent

**File:** `source-updater.md`

**Purpose:** Updates or adds OpenAddresses source JSON files for address, parcel, and building data.

**When to use:**
- Adding a new data source for a city, county, or state
- Updating an existing source that has broken links or outdated URLs
- Finding and migrating to better data sources (e.g., from CSV to ESRI FeatureServer)

**How to invoke:**

When you want to update or add a source, tag the agent with your request:

```
@source-updater please update the source for King County, Washington
```

Or:

```
@source-updater add a new source for Burlington, Vermont
```

**What the agent does:**

1. Locates existing source files (if any)
2. Tests current URLs to see if they still work
3. Searches the internet for authoritative data sources
4. Prefers ESRI FeatureServer/MapServer over other formats
5. Validates data availability and content
6. Creates or updates JSON with proper conform mappings
7. Validates against OpenAddresses JSON Schema v2
8. Creates a pull request with one source at a time

**Key features:**
- Prefers ESRI REST services (most reliable)
- Only uses authoritative government sources
- Updates one source per PR for easier review
- Validates all JSON against schema
- Tests URLs before including them
- Documents changes clearly in PR descriptions

**Examples:**

```bash
# Add a new city source
@source-updater add Portland, Maine addresses

# Update a county source
@source-updater update San Diego County, California

# Update a state source
@source-updater update Vermont statewide addresses
```

## Best Practices

1. **One task at a time:** Each agent invocation should handle one location/source
2. **Be specific:** Provide clear location names including state/province and country if needed
3. **Review PRs:** Always review the agent's work before merging
4. **Test locally:** Run `npm test` to validate any changes
5. **Check URLs:** Verify that updated URLs actually work and contain appropriate data

## Agent Guidelines

All agents follow these principles:
- Make minimal, targeted changes
- Follow existing repository patterns and conventions
- Validate all changes before creating PRs
- Document work clearly in commit messages and PR descriptions
- Ask for clarification when uncertain rather than guessing

## Contributing New Agents

If you want to add a new specialized agent:

1. Create a new `.md` file in this directory
2. Write comprehensive instructions for the agent's task
3. Include examples, best practices, and error handling
4. Document the agent in this README
5. Test the agent with real scenarios
6. Submit a PR with your new agent

## Schema and Validation

All source JSON files must conform to OpenAddresses Schema v2:
- Schema definition: `/schema/source_schema_v2.json`
- Run `npm test` to validate sources
- See `/CONTRIBUTING.md` for detailed schema documentation

## Resources

- [OpenAddresses Repository](https://github.com/openaddresses/openaddresses)
- [Contributing Guide](../CONTRIBUTING.md)
- [Attribute Functions](../ATTRIBUTE_FUNCTIONS.md)
- [OpenAddresses Website](https://openaddresses.io/)
- [Data Portal](https://batch.openaddresses.io/)
