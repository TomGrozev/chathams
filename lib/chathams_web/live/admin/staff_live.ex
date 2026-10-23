defmodule ChathamsWeb.Admin.StaffLive do
  alias Chathams.Accounts.Staff

  use Blank.AdminPage,
    schema: Staff,
    icon: "hero-users",
    index_fields: [:sid, :full_name, :balance],
    show_fields: [:sid, :full_name, :balance, :purchases],
    edit_fields: [:sid, :first_name, :last_name]
end
