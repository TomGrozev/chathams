defmodule ChathamsWeb.SheetController do
  alias Chathams.Accounts
  use ChathamsWeb, :controller

  @blank_row_pages 3

  def blank(conn, _params) do
    staff =
      Accounts.list_staff()
      |> Enum.chunk_every(10)
      |> add_blank()

    conn
    |> assign(:staff, staff)
    |> render(:blank)
  end

  defp add_blank(staff) do
    blank = %{
      sid: {:safe, String.duplicate("&nbsp", 20)},
      full_name: {:safe, String.duplicate("&nbsp", 30)}
    }

    rows = List.duplicate(blank, 10)

    staff ++ List.duplicate(rows, @blank_row_pages)
  end
end
