defmodule ChathamsWeb.StaffLive.Index do
  use ChathamsWeb, :live_view

  alias Chathams.Accounts

  @impl true
  def render(assigns) do
    ~H"""
    <Layouts.app flash={@flash}>
      <.header>
        Listing Staff
        <:actions>
          <.button variant="primary" navigate={~p"/staff/new"}>
            <.icon name="hero-plus" /> New Staff
          </.button>
        </:actions>
      </.header>

      <.table
        id="staff"
        rows={@streams.staff_collection}
        row_click={fn {_id, staff} -> JS.navigate(~p"/staff/#{staff}") end}
      >
        <:col :let={{_id, staff}} label="Sid">{staff.sid}</:col>
        <:col :let={{_id, staff}} label="First name">{staff.first_name}</:col>
        <:col :let={{_id, staff}} label="Last name">{staff.last_name}</:col>
        <:col :let={{_id, staff}} label="Balance">{staff.balance}</:col>
        <:action :let={{_id, staff}}>
          <div class="sr-only">
            <.link navigate={~p"/staff/#{staff}"}>Show</.link>
          </div>
          <.link navigate={~p"/staff/#{staff}/edit"}>Edit</.link>
        </:action>
        <:action :let={{id, staff}}>
          <.link
            phx-click={JS.push("delete", value: %{id: staff.id}) |> hide("##{id}")}
            data-confirm="Are you sure?"
          >
            Delete
          </.link>
        </:action>
      </.table>
    </Layouts.app>
    """
  end

  @impl true
  def mount(_params, _session, socket) do
    {:ok,
     socket
     |> assign(:page_title, "Listing Staff")
     |> stream(:staff_collection, list_staff())}
  end

  @impl true
  def handle_event("delete", %{"id" => id}, socket) do
    staff = Accounts.get_staff!(id)
    {:ok, _} = Accounts.delete_staff(staff)

    {:noreply, stream_delete(socket, :staff_collection, staff)}
  end

  defp list_staff() do
    Accounts.list_staff()
  end
end
