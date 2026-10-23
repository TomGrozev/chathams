defmodule ChathamsWeb.StaffLive.Form do
  use ChathamsWeb, :live_view

  alias Chathams.Accounts
  alias Chathams.Accounts.Staff

  @impl true
  def render(assigns) do
    ~H"""
    <Layouts.app flash={@flash}>
      <.header>
        {@page_title}
        <:subtitle>Use this form to manage staff records in your database.</:subtitle>
      </.header>

      <.form for={@form} id="staff-form" phx-change="validate" phx-submit="save">
        <.input field={@form[:sid]} type="text" label="Sid" />
        <.input field={@form[:first_name]} type="text" label="First name" />
        <.input field={@form[:last_name]} type="text" label="Last name" />
        <.input field={@form[:balance]} type="number" label="Balance" step="any" />
        <footer>
          <.button phx-disable-with="Saving..." variant="primary">Save Staff</.button>
          <.button navigate={return_path(@return_to, @staff)}>Cancel</.button>
        </footer>
      </.form>
    </Layouts.app>
    """
  end

  @impl true
  def mount(params, _session, socket) do
    {:ok,
     socket
     |> assign(:return_to, return_to(params["return_to"]))
     |> apply_action(socket.assigns.live_action, params)}
  end

  defp return_to("show"), do: "show"
  defp return_to(_), do: "index"

  defp apply_action(socket, :edit, %{"id" => id}) do
    staff = Accounts.get_staff!(id)

    socket
    |> assign(:page_title, "Edit Staff")
    |> assign(:staff, staff)
    |> assign(:form, to_form(Accounts.change_staff(staff)))
  end

  defp apply_action(socket, :new, _params) do
    staff = %Staff{}

    socket
    |> assign(:page_title, "New Staff")
    |> assign(:staff, staff)
    |> assign(:form, to_form(Accounts.change_staff(staff)))
  end

  @impl true
  def handle_event("validate", %{"staff" => staff_params}, socket) do
    changeset = Accounts.change_staff(socket.assigns.staff, staff_params)
    {:noreply, assign(socket, form: to_form(changeset, action: :validate))}
  end

  def handle_event("save", %{"staff" => staff_params}, socket) do
    save_staff(socket, socket.assigns.live_action, staff_params)
  end

  defp save_staff(socket, :edit, staff_params) do
    case Accounts.update_staff(socket.assigns.staff, staff_params) do
      {:ok, staff} ->
        {:noreply,
         socket
         |> put_flash(:info, "Staff updated successfully")
         |> push_navigate(to: return_path(socket.assigns.return_to, staff))}

      {:error, %Ecto.Changeset{} = changeset} ->
        {:noreply, assign(socket, form: to_form(changeset))}
    end
  end

  defp save_staff(socket, :new, staff_params) do
    case Accounts.create_staff(staff_params) do
      {:ok, staff} ->
        {:noreply,
         socket
         |> put_flash(:info, "Staff created successfully")
         |> push_navigate(to: return_path(socket.assigns.return_to, staff))}

      {:error, %Ecto.Changeset{} = changeset} ->
        {:noreply, assign(socket, form: to_form(changeset))}
    end
  end

  defp return_path("index", _staff), do: ~p"/staff"
  defp return_path("show", staff), do: ~p"/staff/#{staff}"
end
