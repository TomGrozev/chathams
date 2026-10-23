defmodule ChathamsWeb.PageController do
  use ChathamsWeb, :controller

  def home(conn, _params) do
    render(conn, :home)
  end
end
