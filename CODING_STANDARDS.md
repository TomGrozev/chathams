# Coding standards

Repo-specific rules for chathams. Rules for every Elixir and Phoenix repo live in the stack packs (`rule://stack-elixir`, `rule://stack-phoenix`). Each line here is a rule a reviewer can check against one diff hunk.

- Configure admin screens with `use Blank.AdminPage`, and put display metadata in `@derive Blank.Schema` on the schema (`lib/chathams_web/live/admin/sheets_live.ex:4`, `lib/chathams/accounts/staff.ex:5`).
- Mount every admin page inside the `blank_admin` router macro (`lib/chathams_web/router.ex:30`).
