defmodule ChathamsWeb.StaffLive.Show do
  use ChathamsWeb, :live_view

  alias Chathams.Accounts

  @impl true
  def render(assigns) do
    ~H"""
    <Layouts.app flash={@flash}>
      <.header>
        Staff {@staff.id}
        <:subtitle>This is a staff record from your database.</:subtitle>
        <:actions>
          <.button navigate={~p"/staff"}>
            <.icon name="hero-arrow-left" />
          </.button>
          <.button variant="primary" navigate={~p"/staff/#{@staff}/edit?return_to=show"}>
            <.icon name="hero-pencil-square" /> Edit staff
          </.button>
        </:actions>
      </.header>

      <.list>
        <:item title="Sid">{@staff.sid}</:item>
        <:item title="First name">{@staff.first_name}</:item>
        <:item title="Last name">{@staff.last_name}</:item>
        <:item title="Balance">{@staff.balance}</:item>
      </.list>
    </Layouts.app>
    """
  end

  @impl true
  def mount(%{"id" => id}, _session, socket) do
    {:ok,
     socket
     |> assign(:page_title, "Show Staff")
     |> assign(:staff, Accounts.get_staff!(id))}
  end
end
