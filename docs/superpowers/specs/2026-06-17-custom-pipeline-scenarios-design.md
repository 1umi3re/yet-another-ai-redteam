# Custom Pipeline Scenarios Design

## Goal

Allow admins to save a custom automated-test pipeline from the `New run` page as a reusable scenario.

## Scope

The saved scenario stores only the pipeline structure:

- native executor refs
- converter-backed method refs
- scorer refs
- optional sampling settings
- optional timeout

It does not store the currently selected target or dataset. Those remain selected when a run is created from the saved scenario.

## Backend Design

Add a `custom_scenarios` table with `id`, `name`, `description`, `tags_json`, `template_json`, and timestamps. `template_json` contains the target/dataset-independent runspec fragment.

`GET /api/scenarios` returns built-in scenarios plus persisted custom scenarios. Custom scenario ids are prefixed with `custom:` in the API response and render route, so they cannot collide with built-in registry ids.

`POST /api/scenarios/custom` validates and saves a custom scenario. The request includes `name`, `description`, `tags`, and a pipeline template. The server rejects templates without attack methods or scorers.

`POST /api/scenarios/{scenario_id}/runspec` supports both built-in scenarios and `custom:{id}` scenarios. For custom scenarios, it injects `target_config_id` and `dataset_config_id` into the saved template when rendering.

## Frontend Design

In custom mode, add `Save as scenario` to the Pipeline card header. Clicking it opens an inline modal with name, description, and comma-separated tags. On save, the page posts the current pipeline template to `POST /api/scenarios/custom`, refreshes scenarios, switches to preset mode, and selects the newly created scenario.

The UI uses existing card, button, input, textarea, toast, and modal-like fixed overlay patterns. No new visual language is introduced.

## Testing

Backend integration tests cover custom scenario creation, list output, and runspec rendering with fresh target/dataset ids.

Frontend unit tests cover converting current custom pipeline state into the custom scenario creation payload without target/dataset ids.
