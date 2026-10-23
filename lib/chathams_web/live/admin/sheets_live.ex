defmodule ChathamsWeb.Admin.SheetsLive do
  alias Chathams.Ledger.Sheet

  use Blank.AdminPage,
    schema: Sheet,
    icon: "hero-table-cells",
    index_fields: [:inserted_at],
    index_buttons: [
      import: nil,
      generate: [
        icon: "hero-plus",
        variant: "primary",
        text: "Generate blank sheet",
        action: :navigate,
        path: "sheet/blank"
      ]
    ]

  @impl Blank.AdminPage
  def render_new(assigns) do
    ~H"""
    <.simple_form
      for={to_form(%{})}
      id="upload-form"
      phx-change="validate_upload"
      phx-submit="parse"
    >
      <label
        for={@uploads.sheet_file.ref}
        phx-drop-target={@uploads.sheet_file.ref}
        class={[
          "relative cursor-pointer block w-full rounded-lg border-2 border-gray-300 p-12 text-center flex items-center justify-center focus:outline-none",
          if(@uploads.sheet_file.entries == [], do: "border-dashed hover:border-gray-400", else: "")
        ]}
      >
        <div class={@uploads.sheet_file.entries != [] && "hidden"}>
          <.icon name="hero-arrow-up-tray" class="mx-auto h-12 w-12 text-base-content/40" />
          <p class="mb-2 text-sm">
            <span class="font-semibold">Click to upload</span> or drag and drop
          </p>
          <p class="text-xs">
            PDF
          </p>
        </div>

        <div :for={entry <- @uploads.sheet_file.entries} class="flex items-center space-x-4">
          <.icon name="hero-document-chart-bar" class="w-24 h-24" />
          <div>
            <p>{entry.client_name}</p>
            <button
              type="button"
              phx-click="cancel-upload"
              phx-value-ref={entry.ref}
              aria-label="cancel"
              class="flex items-center text-rose-500"
            >
              <.icon name="hero-x-mark" class="w-5 h-5" /> Remove
            </button>
          </div>
        </div>
        <.live_file_input upload={@uploads.sheet_file} class="hidden" />
      </label>

      <div :for={err <- upload_errors(@uploads.sheet_file)} class="rounded-md bg-rose-50 p-4 my-4">
        <div class="flex">
          <div class="flex-shrink-0">
            <.icon name="hero-exclamation-triangle" class="h-5 w-5
        text-rose-400" />
          </div>
          <div class="ml-3">
            <div class="mt-2 text-sm text-rose-700">
              <p>
                {error_to_string(err)}
              </p>
            </div>
          </div>
        </div>
      </div>

      <:actions>
        <.button
          class="btn btn-primary ml-auto"
          disabled={@uploads.sheet_file.entries == []}
          phx-disable-with="Saving..."
        >
          Load Sheet
        </.button>
      </:actions>
    </.simple_form>
    """
  end

  @impl Blank.AdminPage
  def admin_hook(:mount, _params, socket) do
    allow_upload(socket, :sheet_file, accept: ~w(.pdf), max_entries: 1)
  end

  def admin_hook({:handle_event, "validate_upload"}, _params, socket), do: socket

  def admin_hook({:handle_event, "parse"}, _params, socket) do
    consume_uploaded_entries(socket, :sheet_file, fn %{path: path}, _entry ->
      Chathams.TableReader.process(path)
      {:ok, []}
    end)

    socket
  end

  defp error_to_string(:too_large), do: "Too large"
  defp error_to_string(:too_many_files), do: "You have selected too many files"
  defp error_to_string(:not_accepted), do: "You have selected an unacceptable file type"
end
